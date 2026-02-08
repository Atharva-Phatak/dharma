"""
OCR Engine Steps

This module provides functions and a ZenML step for performing OCR on images using a multimodal LLM.
It includes utilities for sorting image filenames, extracting page numbers, running inference in batches,
and converting results into a Hugging Face Dataset.

Functions:
    sort_pages_by_number(pages: list[str]) -> list[str]:
        Sorts a list of image filenames by their embedded page numbers.

    extract_page_number(filename: str) -> int:
        Extracts the numeric page number from a filename (e.g., 'page_23.jpg').

    do_inference(
        image_paths: list[str],
        model_path: str,
        max_new_tokens: int,
        batch_size: int
    ) -> list[dict]:
        Runs OCR inference on a list of images using a multimodal LLM, batching requests for efficiency.

    ocr_images(
        endpoint: str,
        bucket: str,
        object_key: str,
        local_path: str,
        model_path: str,
        extract_to: str,
        max_new_tokens: int,
        batch_size: int = 5
    ) -> Dataset:
        ZenML step that downloads a zip of images, extracts them, runs OCR, and returns a Hugging Face Dataset.
"""

import re
from pathlib import Path
from datasets import Dataset

from zenml import step
from helper.logger import setup_logger
from helper.minio import download_from_minio
from helper.minio_paths import get_books_path
from pdf2image import convert_from_path
from data_collection.ocr import ocr_batch

logger = setup_logger(__name__)


def load_pdf_and_extract_images(pdf_path: str, extract_to: str) -> list[str]:
    """
    Loads a PDF file and extracts its pages as images.

    Args:
        pdf_path (str): Path to the PDF file.
        extract_to (str): Directory to save the extracted images.

    Returns:
        list[str]: List of file paths to the extracted images.
    """
    pages = convert_from_path(pdf_path, dpi=300)
    image_paths = []
    for i, page in enumerate(pages):
        image_path = Path(extract_to) / f"page_{i + 1}.jpg"
        page.save(image_path, "JPEG")
        image_paths.append(str(image_path))
    return image_paths


def sort_pages_by_number(pages: list[str]) -> list[str]:
    """
    Sorts a list of image filenames by their embedded page numbers.

    Args:
        pages (list[str]): List of image file paths or names containing 'page_<number>'.

    Returns:
        list[str]: Sorted list of image file paths/names by page number.
    """

    def extract_number(filename: str) -> int:
        match = re.search(r"page_(\d+)", filename)
        return int(match.group(1)) if match else -1

    return sorted(pages, key=extract_number)


@step(enable_step_logs=True, enable_cache=False, name="extract_content")
def ocr_images(
    endpoint: str,
    bucket: str,
    book_name: str,
    model_name: str,
    max_new_tokens: int,
    prompt: str,
    batch_size: int = 5,
) -> Dataset:
    """
    ZenML step that downloads a zip of images from MinIO, extracts them, runs OCR inference,
    and returns the results as a Hugging Face Dataset.

    Args:
        endpoint (str): MinIO endpoint URL.
        bucket (str): MinIO bucket name.
        object_key (str): Object key for the zip file in MinIO.
        local_path (str): Local path to save the downloaded zip file.
        model_path (str): Path to the pretrained multimodal LLM model.
        extract_to (str): Directory to extract images to.
        max_new_tokens (int): Maximum number of tokens to generate per output.
        batch_size (int, optional): Number of images to process per batch. Defaults to 5.
        prompt (str): The prompt to use for the OCR model.

    Returns:
        Dataset: Hugging Face Dataset containing OCR results for each image.
    """
    book_minio_path = get_books_path(book_name=book_name)
    local_path = f"/tmp/{book_name}.pdf"
    local_image_path = f"/tmp/{book_name}_images"
    pdf_path = download_from_minio(
        endpoint=endpoint,
        bucket=bucket,
        minio_path=book_minio_path,
        local_path=local_path,
    )
    logger.info(f"Downloaded PDF from MinIO to {local_path}")

    image_paths = load_pdf_and_extract_images(
        pdf_path=pdf_path, extract_to=local_image_path
    )
    image_paths = sort_pages_by_number(image_paths)
    logger.info(f"Extracted {len(image_paths)} images from {local_image_path}")

    outputs = ocr_batch(
        image_paths=image_paths,
    )

    # Convert list[dict] → Hugging Face Dataset
    dataset = Dataset.from_list(outputs)
    return dataset
