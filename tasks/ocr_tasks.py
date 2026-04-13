import os, re, subprocess
from pathlib import Path
from core.logger import log


_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(
        os.getenv("USERNAME", "")
    ),
]


def _setup_tesseract():
    try:
        import pytesseract
        for path in _TESSERACT_PATHS:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return True
        import shutil
        if shutil.which("tesseract"):
            return True
        return False
    except ImportError:
        return False


_TESSERACT_OK = _setup_tesseract()



def _ocr_image(image) -> str:
    if not _TESSERACT_OK:
        raise RuntimeError(
            "Tesseract not found. Install from: "
            "https://github.com/UB-Mannheim/tesseract/wiki\n"
            "Then run: pip install pytesseract"
        )
    import pytesseract
    text = pytesseract.image_to_string(image, lang="eng")
    return text.strip()


def _clean_ocr_text(text: str) -> str:
    text = re.sub(r"[^\x20-\x7E\n]", "", text)   
    text = re.sub(r"\n{3,}", "\n\n", text)         
    text = re.sub(r" {2,}", " ", text)            
    return text.strip()



def read_screen(raw: str = "") -> str:
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        text       = _ocr_image(screenshot)
        text       = _clean_ocr_text(text)

        if not text:
            return "The screen appears to contain no readable text."

        # Truncate for display
        display = text[:800]
        if len(text) > 800:
            display += f"\n... ({len(text) - 800} more characters)"
        return f"── Screen Text ──\n{display}"

    except RuntimeError as e:
        return str(e)
    except ImportError:
        return "Pillow not installed. Run: pip install Pillow"
    except Exception as e:
        return f"Screen OCR failed: {e}"


def read_clipboard_image() -> str:
    try:
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()

        if img is None:
            return ("No image on clipboard. "
                    "Copy an image first (e.g. screenshot with Win+Shift+S), "
                    "then say 'read clipboard image'.")

        from PIL import Image
        if not isinstance(img, Image.Image):
            return "Clipboard contains data but not an image."

        text = _ocr_image(img)
        text = _clean_ocr_text(text)

        if not text:
            return "Could not extract text from the clipboard image."

        # Copy to clipboard as text
        import pyperclip
        pyperclip.copy(text)

        display = text[:600]
        if len(text) > 600:
            display += f"\n... ({len(text) - 600} more chars)"
        return f"── Text from Clipboard Image ──\n{display}\n\n(Also copied to clipboard as text)"

    except RuntimeError as e:
        return str(e)
    except Exception as e:
        return f"Clipboard OCR failed: {e}"


def read_image_file(path: str) -> str:
    if not os.path.exists(path):
        return f"File not found: {path}"
    try:
        from PIL import Image
        img  = Image.open(path)
        text = _ocr_image(img)
        text = _clean_ocr_text(text)

        if not text:
            return f"No readable text found in: {os.path.basename(path)}"

        import pyperclip
        pyperclip.copy(text)

        return (f"── OCR: {os.path.basename(path)} ──\n"
                f"{text[:600]}"
                + ("\n(copied to clipboard)" if text else ""))

    except Exception as e:
        return f"OCR failed for {path}: {e}"


def capture_and_read_region() -> str:
    
    try:
        from PIL import ImageGrab
        import pyperclip

        full = ImageGrab.grab()
        w, h = full.size
        margin_x = int(w * 0.05)
        margin_y = int(h * 0.08)
        cropped  = full.crop((margin_x, margin_y, w - margin_x, h - margin_y))

        text = _ocr_image(cropped)
        text = _clean_ocr_text(text)

        if not text:
            return "No readable text found in screen region."

        pyperclip.copy(text)

        return (f"── Screen Region Text ──\n{text[:500]}"
                + ("\n... (copied to clipboard)" if text else ""))

    except Exception as e:
        return f"Region OCR failed: {e}"


def ocr_status() -> str:
    lines = []
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        lines.append(f"Tesseract: v{version} — OCR ready ✓")
    except ImportError:
        lines.append("pytesseract: not installed — run: pip install pytesseract")
    except Exception as e:
        lines.append(f"Tesseract: not found — {e}")
        lines.append("  Download from: https://github.com/UB-Mannheim/tesseract/wiki")

    try:
        from PIL import Image
        lines.append("Pillow: installed ✓")
    except ImportError:
        lines.append("Pillow: not installed — run: pip install Pillow")

    return "\n".join(lines)