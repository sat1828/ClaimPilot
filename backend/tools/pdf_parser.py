import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    try:
        import fitz
        doc = fitz.open(file_path)
        text_parts = []
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
        doc.close()
        full_text = "\n".join(text_parts)
        logger.info(f"Parsed PDF: {file_path} ({len(full_text)} chars, {len(text_parts)} pages)")
        return full_text
    except ImportError:
        logger.error("PyMuPDF (fitz) not installed. Falling back to basic extraction.")
        with open(file_path, "r", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to parse PDF {file_path}: {e}")
        raise


def extract_images_from_pdf(file_path: str, output_dir: str) -> list[str]:
    import fitz
    doc = fitz.open(file_path)
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    for page_num, page in enumerate(doc):
        images = page.get_images()
        for img_idx, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            img_path = os.path.join(output_dir, f"page{page_num+1}_img{img_idx+1}.{ext}")
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            image_paths.append(img_path)
    doc.close()
    logger.info(f"Extracted {len(image_paths)} images from {file_path}")
    return image_paths


def transcribe_audio(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    try:
        from openai import OpenAI
        from config import settings
        client = OpenAI(api_key=settings.openai_api_key)
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=settings.whisper_model,
                file=audio_file,
            )
        logger.info(f"Transcribed audio: {file_path} ({len(transcript.text)} chars)")
        return transcript.text
    except ImportError:
        logger.warning("OpenAI not installed, returning mock transcript")
        return f"[MOCK TRANSCRIPT] Simulated transcription of {file_path}. Claimant describes an incident requiring insurance coverage."
    except Exception as e:
        logger.error(f"Failed to transcribe audio {file_path}: {e}")
        return f"[TRANSCRIPTION ERROR: {e}]"
