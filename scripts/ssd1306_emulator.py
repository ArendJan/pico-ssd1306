#!/usr/bin/env python3
import numpy as np
from pathlib import Path
import subprocess

def load_font(path: Path, extended: bool = False) -> bytes:
        command = "gcc -E"
        if extended:
            command += " -D SSD1306_ASCII_FULL"
        header = subprocess.run(
            [*command.split(" "), path], stdout=subprocess.PIPE
        ).stdout.decode()

        # Process the header
        header = header[header.index("[] = {") + 5 :]

        header = header.replace("\n\n", " ")

        header = header[: header.rfind(";")].replace(',', ' ')#.replace('0x', '')
        header = header.replace("{", "").replace("}", "").replace("// font width, height", "").replace('\n', ' ')
        return bytes(map(lambda n: int(n, base=16),header.split()))

class SSD1306:
    def __init__(self, width: int = 128, height: int = 64):
        self._screen = np.zeros((height, width), dtype=bool)
        self._width = width
        self._height = height

    def clear(self):
        self._screen[:, :] = False

    def set_pixel(self, x: int, y: int, mode=None):
        self._screen[y, x] = True

    def draw_text(
        self,
        font: bytes,
        text: bytes,
        anchor_x: int,
        anchor_y: int,
        mode=None,
        rotation: int = 0,
    ):
        if not font or not text:
            return

        font_width: int = font[0]

        n: int = 0
        font_height: int = font[1]
        line_no: int = 0
        x_offset: int = 0

        for byte in text:
            if byte == b"\n"[0]:
                line_no += 1
                n += 1
                x_offset = 0
                continue

            if anchor_x + (x_offset * font_width) >= self._width:
                line_no += 1
                anchor_x = 0
                x_offset = 0

            match rotation:
                case 0:
                    self.draw_char(
                        font,
                        byte,
                        anchor_x + (x_offset * font_width),
                        anchor_y + (font_height * line_no),
                        mode,
                        rotation,
                    )

                case 90:
                    self.draw_char(
                        font,
                        byte,
                        anchor_x,
                        anchor_y + (n * font_width),
                        mode,
                        rotation,
                    )
                case _:
                    raise ValueError("Invalid Rotation")

            x_offset += 1
            n += 1

    def draw_char(
        self,
        font: bytes,
        c: int,
        anchor_x: int,
        anchor_y: int,
        mode=None,
        rotation: int = 0,
    ):
        if not font or c < 32:
            return

        font_width: int = font[0]
        font_height: int = font[1]

        n_bytes: int = (font_width * font_height // 8) + (
            1 if (font_width * font_height % 8) else 0
        )

        seek: int = (c - 32) * n_bytes + 2

        b_seek: int = 0

        for x in range(font_width):
            for y in range(font_height):
                if font[seek] >> b_seek & 0b00000001:
                    match rotation:
                        case 0:
                            self.set_pixel(x + anchor_x, y + anchor_y, mode)
                        case 90:
                            self.set_pixel(
                                -y + anchor_x + font_height, x + anchor_y, mode
                            )
                        case _:
                            raise ValueError("Invalid Rotation")

                b_seek += 1
                if b_seek == 8:
                    b_seek = 0
                    seek += 1

    def __str__(self) -> str:
        top_border = "+" + "-" * self._width * 2 + "+\n"
        rows = [
            "|"
            + "".join(
                "\x1b[107m  \x1b[0m" if pixel else "\x1b[40m  \x1b[0m" for pixel in row
            )
            + "|"
            for row in self._screen
        ]

        assert len(rows) == self._height

        return top_border + "\n".join(rows) + "\n" + top_border
