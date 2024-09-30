#!/usr/bin/env python3
from ssd1306_emulator import SSD1306, load_font

from custom_font import CustomFont

from PIL import ImageFont


def main():
    fonts = {
        "5x8": load_font("../textRenderer/5x8_font.h"),
        "8x8": load_font("../textRenderer/8x8_font.h", extended=True),
        "12x16": load_font("../textRenderer/12x16_font.h"),
        "16x32": load_font("../textRenderer/16x32_font.h"),
        "custom_export": load_font("../textRenderer/font_courB08_6x11.h"),
        "custom": CustomFont.from_font(ImageFont.load_default())._bytes,
    }

    texts = {
        "KaasBaas": b"Kaas is de baas\nDit is een Mock Display",
        "KaasKlant": b"Ik wil kaas!",
        "Kaas": b"Kaas\nKaas",
        "IP": b"mirte-XXXXX\nIP: 192.168.42.1",
        "mirte": b"IPs: 192.168.120.42\nHn: Mirte-123456\nWi-Fi:Mirte-123456\nSOC: 50%\n2024-09-26T22:49:19",
    }

    oled = SSD1306()
    oled.draw_text(fonts["custom_export"], texts["mirte"], 1, 1)

    print(oled)


if __name__ == "__main__":
    main()
