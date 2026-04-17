from paddleocr import PaddleOCR
import cv2
import numpy as np

ocr = PaddleOCR(use_angle_cls=True, lang='en')

def extract_ocr(image_bytes):
    img = cv2.imdecode(
        np.frombuffer(image_bytes, np.uint8),
        cv2.IMREAD_COLOR
    )

    if img is None:
        return {
            "raw_text": "",
        }

    result = ocr.ocr(img)

    texts = []
    confidences = []

    if result:
        for block in result:
            if not block:
                continue

            for line in block:
                try:
                    content = line[1]

                    if isinstance(content, (list, tuple)) and len(content) == 2:
                        text, conf = content
                        texts.append(str(text))
                        if isinstance(conf, (float, int)):
                            confidences.append(float(conf))

                    elif isinstance(content, str):
                        texts.append(content)

                except Exception:
                    continue

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    return {
        "raw_text": "\n".join(texts),
        "ocr_confidence": round(avg_conf, 2)
    }
