import base64
import time
from helper.logger import setup_logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
import logging
from openai import OpenAI


logger = setup_logger(__name__)

# Configuration matching your vLLM setup
IMAGES_PER_REQUEST = 5  # matches limit_mm_per_prompt
MAX_WARMUP_WAIT = 600


def encode_image(image_path: str) -> str:
    """Encode a single image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    after=after_log(logger, logging.INFO),
)
def ocr_multiple_images(
    image_base64_list: list[str], model_name: str, client: OpenAI
) -> str:
    """
    Process multiple images (up to 5) in a single request.

    Args:
        image_base64_list: List of base64-encoded images (max 5)


    Returns:
        Single OCR result containing text from all images
    """
    if len(image_base64_list) > IMAGES_PER_REQUEST:
        raise ValueError(
            f"Cannot process more than {IMAGES_PER_REQUEST} images per request"
        )

    # Build content with multiple images
    content = []

    # Add all images
    for img_base64 in image_base64_list:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_base64}"},
            }
        )

    # Add single instruction for all images
    content.append(
        {
            "type": "text",
            "text": "Extract the text from the above document as if you were reading it naturally. Page numbers should be wrapped in brackets. Ex: <page_number>14</page_number> or <page_number>9/22</page_number>. Prefer using ☐ and ☑ for check boxes.",
        }
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        temperature=0.0,
        max_tokens=15000,
    )

    return response.choices[0].message.content


def check_first_batch(image_batch: list, model_name: str, client: OpenAI):
    """Method to check if vllm is ready for processing batches.
    Args:
        image_batch: List of image file paths
    """
    encoded_images = [encode_image(image_batch[0])]
    # encoded_images = [encode_image(path) for path in image_batch]

    # Send request with multiple images
    ocr_result = ocr_multiple_images(
        encoded_images, model_name=model_name, client=client
    )
    if len(ocr_result) > 0:
        return True
    else:
        return False


def wait_for_model_ready(
    client: OpenAI,
    image_batch: list,
    model_name: str,
    max_wait: int = MAX_WARMUP_WAIT,
    check_interval: int = 5,
) -> bool:
    start_time = time.time()
    logger.info(f"Waiting for model '{model_name}' to be ready...")

    while (time.time() - start_time) < max_wait:
        try:
            is_up = check_first_batch(
                image_batch=image_batch,
                model_name=model_name,
                client=client,
            )
            if is_up:
                elapsed = time.time() - start_time
                logger.info(f"✓ Model '{model_name}' is ready! (took {elapsed:.1f}s)")
                return True  # ← FIX #1
            else:
                logger.warning(f"{model_name} is not up yet")

        except Exception as e:  # ← FIX #2: Catch all exceptions during warmup
            logger.info(f"Model not ready: {e}. Waiting for pod to start...")

        # Wait before next check
        elapsed = time.time() - start_time
        logger.info(
            f"Waiting... ({elapsed:.0f}s / {max_wait}s) - "
            f"next check in {check_interval}s"
        )
        time.sleep(check_interval)

    # Timeout
    logger.error(
        f"✗ Timeout: Model did not become ready within {max_wait}s. "
        f"Pod may have failed to start."
    )
    return False


def ocr_batch(
    image_paths: list[str],
    images_per_request: int = IMAGES_PER_REQUEST,
    show_progress: bool = True,
) -> list[dict]:
    """
    Process a batch of images sequentially.
    With maxNumSeqs=1, requests are processed one at a time.

    Args:
        image_paths: List of image file paths
        images_per_request: Number of images per request (default: 5)
        show_progress: Show progress updates

    Returns:
        List of dicts with image_paths (list), ocr_result, status, error
    """
    # Split images into chunks
    image_chunks = [
        image_paths[i : i + images_per_request]
        for i in range(0, len(image_paths), images_per_request)
    ]

    total_requests = len(image_chunks)
    logger.info(f"Processing {len(image_paths)} images in {total_requests} requests")
    results = []
    start_time = time.time()

    vllm_router_url = "http://vllm-stack-router-service.zenml.svc.cluster.local/v1"
    model_name = "/models/Nanonets-OCR2-3B"
    client: OpenAI = OpenAI(
        base_url=vllm_router_url,
        api_key="dummy",
    )

    is_vllm_alive = wait_for_model_ready(
        image_batch=image_chunks[0], client=client, model_name=model_name
    )
    if is_vllm_alive:
        logger.info("Testing dummy batch")
        is_vllm_ready_for_batching = check_first_batch(
            image_batch=image_chunks[0],
            model_name=model_name,
            client=client,
        )
        if not is_vllm_ready_for_batching:
            raise ValueError(f"Model '{model_name}' is not ready yet. ")
    else:
        raise ValueError(f"Model {model_name} is not ready yet. ")

    for request_num, chunk_paths in enumerate(image_chunks, 1):
        chunk_start = time.time()

        try:
            # Encode all images in the chunk
            encoded_images = [encode_image(path) for path in chunk_paths]

            # Send request with multiple images
            ocr_result = ocr_multiple_images(
                encoded_images, model_name=model_name, client=client
            )

            results.append(
                {
                    "image_paths": chunk_paths,
                    "ocr_result": ocr_result,
                    "status": "success",
                    "error": None,
                    "num_images": len(chunk_paths),
                }
            )

            chunk_time = time.time() - chunk_start

            if show_progress:
                elapsed = time.time() - start_time
                avg_time = elapsed / request_num
                remaining = (total_requests - request_num) * avg_time
                logger.info(
                    f"✓ Request {request_num}/{total_requests} ({len(chunk_paths)} images) "
                    f"completed in {chunk_time:.2f}s | Est. remaining: {remaining:.1f}s"
                )

        except Exception as e:
            logger.info(f"✗ Request {request_num}/{total_requests} FAILED: {e}")
            results.append(
                {
                    "image_paths": chunk_paths,
                    "ocr_result": None,
                    "status": "failed",
                    "error": str(e),
                    "num_images": len(chunk_paths),
                }
            )

    total_time = time.time() - start_time
    successful_requests = sum(1 for r in results if r["status"] == "success")
    # successful_images = sum(
    #    r["num_images"] for r in results if r["status"] == "success"
    # )

    logger.info(f"Total processing time: {total_time:.2f}s")
    logger.info(f"Successful requests: {successful_requests}/{total_requests}")
    logger.info(f"Average time per request: {total_time / total_requests:.2f}s")
    logger.info(f"Average time per image: {total_time / len(image_paths):.2f}s")
    return results
