#!/usr/bin/env python3
from custom_font import CustomFont

if __name__ == "__main__":
    font = CustomFont.load_header("textRenderer/font_courB08_6x11.h", extended=True)

    font.get_pil_image_char(b"a"[0]).show()
    font.get_pil_image_char(b"p"[0]).show()
    font.get_pil_image_char(b"E"[0]).show()