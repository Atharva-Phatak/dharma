from zenml import pipeline

from helper.logger import setup_logger
from helper.pipeline_settings.data_collection import (
    docker_settings,
    k8s_operator_settings,
)
import argparse
from data_collection.extract_data import ocr_images
from data_collection.upload import store_extracted_texts_to_minio
from helper.constants import DefaultConstants
logger = setup_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Run OCR ZenML pipeline")
    parser.add_argument("--endpoint", type=str, required=True)
    parser.add_argument("--bucket", type=str, required=True)
    parser.add_argument("--book_name", type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    parser.add_argument("--batch_size", type=int, default=5)
    parser.add_argument("--prompt", type=str, default="Extract all text from the image")
    return parser.parse_args()


@pipeline(
    settings={
        "docker": docker_settings,
        "orchestrator": k8s_operator_settings,
    },
    name="ocr_pipeline",
)
def ocr_pipeline(
    bucket: str,
    book_name: str,
    model_name: str,
    max_new_tokens: int,
    prompt: str,
    batch_size: int,
):
    """Pipeline for performing OCR on images extracted from a zip file."""
    logger.info("Starting OCR pipeline")
    data = ocr_images(
        endpoint=DefaultConstants.minio_endpoint.value,
        bucket=bucket,
        book_name=book_name,
        model_name=model_name,
        prompt=prompt,
        max_new_tokens=max_new_tokens,
        batch_size = batch_size
    )
    logger.info(f"OCR results stored in MinIO bucket '{bucket}'.")
    store_extracted_texts_to_minio(
        dataset=data,
        bucket_name=bucket,
        minio_endpoint=DefaultConstants.minio_endpoint.value,
        filename=book_name,
    )
    logger.info(
        f"OCR results stored in MinIO bucket '{bucket}' with filename '{book_name}'."
    )

if __name__ == "__main__":
    parser = parse_args()
    ocr_pipeline(
        endpoint=parser.endpoint,
        bucket=parser.bucket,
        book_name=parser.book_name,
    )