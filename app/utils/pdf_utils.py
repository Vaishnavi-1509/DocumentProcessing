import fitz
import base64

def pdf_to_base64_images(pdf_bytes: bytes, dpi: int = 100) -> list[str]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        encoded = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        images.append(encoded)
    doc.close()
    return images
