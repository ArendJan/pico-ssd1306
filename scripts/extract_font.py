#!/usr/bin/env python3
from custom_font import CustomFont
from PIL import ImageFont

if __name__ == "__main__":
    font = ImageFont.load_default()

    my_font = CustomFont.from_font(font, extended=True)
    # my_font.get_pil_image_char(b"!"[0]).show()
    print(CustomFont.from_font(font, extended=True).create_header("font_courB08"))
