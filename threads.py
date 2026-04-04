"""
ComicEditor — Arka plan iş parçacığı: Otomatik OCR + Çeviri + İnpaint
"""
import cv2  # type: ignore
import numpy as np  # type: ignore
import easyocr  # type: ignore
from PyQt6.QtGui import QImage  # type: ignore
from PyQt6.QtCore import QThread, pyqtSignal  # type: ignore


class AutoScanlationThread(QThread):
    """Tam otonom metin tespiti, silme ve çeviri işlemini yürüten thread."""
    finished = pyqtSignal(tuple)
    progress = pyqtSignal(str)

    def __init__(self, qimage, settings):
        super().__init__()
        self.qimage = qimage
        self.settings = settings

    def run(self):
        self.progress.emit("Metin Blokları Çözümleniyor...")
        qimg = self.qimage.convertToFormat(QImage.Format.Format_RGB32)
        width, height = qimg.width(), qimg.height()
        ptr = qimg.constBits()
        ptr.setsize(height * width * 4)
        arr = np.array(ptr).reshape((height, width, 4))
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)

        try:
            reader = easyocr.Reader(['en'], gpu=True)
        except Exception:
            reader = easyocr.Reader(['en'], gpu=False)

        ocr_results = reader.readtext(
            img_bgr, paragraph=True, text_threshold=0.4,
            mag_ratio=2.0, bbox_min_score=0.3, x_ths=0.7, y_ths=0.7
        )

        h_img, w_img, _ = img_bgr.shape
        full_mask = np.zeros((h_img, w_img), dtype=np.uint8)

        results = []
        for i, (bbox, text) in enumerate(ocr_results, 1):
            text = text.strip()
            if len(text) < 2:
                continue

            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            x, y = int(min(x_coords)), int(min(y_coords))
            w, h_box = int(max(x_coords) - x), int(max(y_coords) - y)
            results.append({"rect": (x, y, w, h_box), "text": text})

            pad = 2
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2, y2 = min(w_img, x + w + pad), min(h_img, y + h_box + pad)
            crop = img_bgr[y1:y2, x1:x2]
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            box_mask = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 15, 6
            )

            kernel_local = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            box_mask = cv2.dilate(box_mask, kernel_local, iterations=1)
            full_mask[y1:y2, x1:x2] = cv2.bitwise_or(
                full_mask[y1:y2, x1:x2], box_mask
            )

        if not results:
            self.finished.emit((cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), []))
            return

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        full_mask = cv2.dilate(full_mask, kernel, iterations=1)

        self.progress.emit("Tüm orijinal metinler tek seferde pürüzsüzce siliniyor...")
        cleaned_bgr = cv2.inpaint(img_bgr, full_mask, 4, cv2.INPAINT_TELEA)

        self.progress.emit("Yapay Zeka (AI) Çeviri İşlemi Devrede...")
        engine = str(self.settings.get("engine", "Otomatik (Gemini > Google)"))
        api_key = str(self.settings.get("api_key", "")).strip()

        texts_to_translate: dict = {
            str(i): r["text"] for i, r in enumerate(results)
        }
        translated_dict: dict[str, str] = {}

        if api_key and "Gemini" in engine:
            try:
                import google.generativeai as genai  # type: ignore
                import json
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content((
                    "Sen profesyonel bir çizgi roman ve manga çevirmenisin, "
                    "tüm argo ve kalıpları Türkçe'ye harika uyarla.\n"
                    "ASLA açıklama YAPMA! SADECE JSON ÇEVİR.\n"
                    + json.dumps(texts_to_translate)
                ))
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_text)
                if isinstance(parsed, dict):
                    for k, v in parsed.items():
                        translated_dict[str(k)] = str(v)
            except Exception:
                pass

        if not translated_dict:
            self.progress.emit("Google Ücretsiz Çeviri Kullanılıyor...")
            try:
                from deep_translator import GoogleTranslator  # type: ignore
                translator = GoogleTranslator(source='en', target='tr')
                for i, r in enumerate(results):
                    translated_dict[str(i)] = str(translator.translate(r["text"]))
            except Exception:
                pass

        for i, res in enumerate(results):
            res["translated_text"] = translated_dict.get(str(i), res["text"])

        self.finished.emit((cv2.cvtColor(cleaned_bgr, cv2.COLOR_BGR2RGB), results))
