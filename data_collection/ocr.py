import torch
from PIL import Image
import time
from transformers import LightOnOcrForConditionalGeneration, LightOnOcrProcessor
from pathlib import Path
import re
def extract_page_number(filename: str) -> int:
     """
     Extracts the numeric page number from a filename like 'page_23.jpg'.

     Args:
         filename (str): The filename or path containing the page number.

     Returns:
         int: The extracted page number.

     Raises:
         ValueError: If the filename does not match the expected format.
     """
     match = re.search(r"page_(\d+)", Path(filename).stem)
     if match:
         return int(match.group(1))
     raise ValueError(f"Invalid filename format for page number: {filename}")

def do_inference(
        image_paths: list[str],
        model_path: str,
        max_new_tokens: int,
        batch_size: int,
        prompt: str,
) -> list[dict]:
    """
    Runs OCR inference on image paths using LightOnOCR with batching.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32

    # 1. Load Model and Processor
    model = LightOnOcrForConditionalGeneration.from_pretrained(
        model_path, torch_dtype=dtype
    ).to(device)

    processor = LightOnOcrProcessor.from_pretrained(model_path)
    processor.tokenizer.padding_side = "left"  # Required for batching

    generated_texts = []
    total_images = len(image_paths)
    start_time = time.time()

    # 2. Process in batches
    for indx in range(0, total_images, batch_size):
        batch_paths = image_paths[indx: indx + batch_size]

        # Prepare the conversation format for the processor
        conversations = []
        for img_path in batch_paths:
            # We open the image here as requested
            image = Image.open(img_path).convert("RGB")
            conversations.append([
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},  # Passing PIL object directly
                        {"type": "text", "text": prompt}
                    ]
                }
            ])

        # 3. Preprocess the batch
        inputs = processor.apply_chat_template(
            conversations,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            padding=True
        )

        # Move tensors to device
        inputs = {k: v.to(device=device, dtype=dtype) if v.is_floating_point() else v.to(device)
                  for k, v in inputs.items()}

        # 4. Generate
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False  # Standard for OCR to keep it deterministic
            )

        # 5. Decode only the new tokens
        input_len = inputs["input_ids"].shape[1]
        generated_ids = output_ids[:, input_len:]
        batch_outputs = processor.batch_decode(generated_ids, skip_special_tokens=True)

        # 6. Format results
        for img_path, text in zip(batch_paths, batch_outputs):
            page_no = extract_page_number(img_path)  # Assuming this helper exists
            generated_texts.append({
                "page": page_no,
                "content": text.strip(),
            })

        print(f"Processed {min(indx + batch_size, total_images)}/{total_images} images...")

    print(f"Total time: {time.time() - start_time:.2f}s")
    return generated_texts