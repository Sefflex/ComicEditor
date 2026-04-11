"""
ComicEditor — Yardımcı fonksiyonlar ve sabitler
"""
import os
import ssl
import platform
import rarfile  # type: ignore

# ── Proje kök dizini ──
base_dir = os.path.dirname(os.path.abspath(__file__))

# ── Platform'a göre unrar yapılandırması ──
if platform.system() == "Darwin":
    if platform.machine() == "arm64":
        rarfile.UNRAR_TOOL = os.path.join(base_dir, "unrar_mac_arm", "unrar")
    else:
        rarfile.UNRAR_TOOL = os.path.join(base_dir, "unrar_mac_intel", "unrar")
elif platform.system() == "Windows":
    rarfile.UNRAR_TOOL = os.path.join(base_dir, "unrar_windows", "unrar.exe")

# ── SSL sertifika atlatma (easyocr/deep_translator için) ──
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


def get_font_path(font_name: str) -> str:
    """Verilen font adına göre dosya yolunu döndürür."""
    if "Anime Ace" in font_name:
        return os.path.join(base_dir, "fonts", "animeace.ttf")
    if "Patrick Hand" in font_name:
        return os.path.join(base_dir, "fonts", "PatrickHand.ttf")
    if "Comic Neue" in font_name:
        return os.path.join(base_dir, "fonts", "comic.ttf")

    font_map = {
        "Arial": "Arial.ttf",
        "Comic Sans MS": "Comic Sans MS.ttf",
        "Impact": "Impact.ttf",
        "Times New Roman": "Times New Roman.ttf",
    }
    return font_map.get(font_name, "Arial.ttf")
