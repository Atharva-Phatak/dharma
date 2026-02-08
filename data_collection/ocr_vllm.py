# from vllm import LLM, EngineArgs, SamplingParams
#
# def extract_page_number(filename: str) -> int:
#     """
#     Extracts the numeric page number from a filename like 'page_23.jpg'.
#
#     Args:
#         filename (str): The filename or path containing the page number.
#
#     Returns:
#         int: The extracted page number.
#
#     Raises:
#         ValueError: If the filename does not match the expected format.
#     """
#     match = re.search(r"page_(\d+)", Path(filename).stem)
#     if match:
#         return int(match.group(1))
#     raise ValueError(f"Invalid filename format for page number: {filename}")
#
# def do_inference(
#     image_paths: list[str],
#     model_path: str,
#     max_new_tokens: int,
#     batch_size: int,
#     prompt: str,
# ) -> list[dict]:
#     """
#     Runs OCR inference on a list of images using a multimodal LLM, batching requests for efficiency.
#
#     Args:
#         image_paths (list[str]): List of image file paths to process.
#         model_path (str): Path to the pretrained multimodal LLM model.
#         max_new_tokens (int): Maximum number of tokens to generate per output.
#         batch_size (int): Number of images to process per batch.
#         prompt (str): The prompt to use for the OCR model.
#
#     Returns:
#         list[dict]: List of dictionaries with 'page' and 'content' keys for each image.
#     """
#     engine_args = EngineArgs(
#         model=model_path,
#         limit_mm_per_prompt={"image": 5, "video": 0},
#         mm_processor_kwargs={"min_pixels": 28 * 28, "max_pixels": 1280 * 80 * 80},
#     )
#     sampling_params = SamplingParams(
#         max_tokens=max_new_tokens,
#     )
#     model = LLM(**asdict(engine_args))
#     generated_texts = []
#     total_batches = len(image_paths) // batch_size
#     start = time.time()
#     for indx in range(0, len(image_paths), batch_size):
#         batch = image_paths[indx : indx + batch_size]
#         inputs = [
#             {
#                 "prompt": prompt,
#                 "multi_modal_data": {
#                     "image": Image.open(img_path).convert("RGB"),
#                 },
#             }
#             for img_path in batch
#         ]
#         outputs = model.generate(inputs, sampling_params=sampling_params)
#         logger.info(f"Processed batch {indx // batch_size}/{total_batches}")
#         for img_path, output in zip(batch, outputs):
#             page_no = extract_page_number(img_path)
#             generated_texts.append(
#                 {
#                     "page": page_no,
#                     "content": output.outputs[0].text,
#                 }
#             )
#     logger.info(
#         f"Generated texts: {len(generated_texts)} in {time.time() - start:.2f} seconds"
#     )
#     return generated_texts