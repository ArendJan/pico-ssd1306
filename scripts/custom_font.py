import subprocess
from dataclasses import dataclass, field, InitVar
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def to_image(txt: str, font: ImageFont.ImageFont, bg=(0,), fg=(255,)) -> Image.Image:
    # make a blank image for the text]
    img = Image.new("1", font.getsize(txt), bg)

    d = ImageDraw.Draw(img)
    d.text((0, 0), txt, font=font, fill=fg)

    return img


@dataclass
class CustomFont:
    width_: InitVar[int]
    height_: InitVar[int]
    extended: bool = False
    _bytes: bytes | bytearray = field(init=False, default_factory=lambda: None)

    def __post_init__(self, width_: int, height_: int):
        end = 256 if self.extended else 127
        n_bytes = ((width_ * height_) // 8) + (width_ * height_ % 8 > 0)
        self._bytes = bytearray([0] * (n_bytes * (end - 32) + 2))
        self._bytes[0] = width_
        self._bytes[1] = height_

    @property
    def width(self) -> int:
        return self._bytes[0]

    @width.setter
    def set_width(self, value: int) -> None:
        if isinstance(self._bytes, bytearray):
            self._bytes[0] = value
        else:
            raise AttributeError("Width is read only!")

    @property
    def height(self) -> int:
        return self._bytes[1]

    @height.setter
    def set_height(self, value: int) -> None:
        if isinstance(self._bytes, bytearray):
            self._bytes[1] = value
        else:
            raise AttributeError("height is read only!")

    def chars(self, c: int) -> bytes:
        seek: int = (c - 32) * self.n_bytes + 2
        return self._bytes[seek: seek + self.n_bytes]

    def get_char_array(self, c: str):
        data = np.zeros((self.height, self.width), dtype=bool)

        if not self._bytes or c < 32:
            return

        seek: int = (c - 32) * self.n_bytes + 2

        b_seek: int = 0

        for x in range(self.width):
            for y in range(self.set_height):
                if self._bytes[seek] >> b_seek & 0b00000001:
                    data[y, x] = True

                b_seek += 1
                if b_seek == 8:
                    b_seek = 0
                    seek += 1

        return data

    def get_pil_image_char(self, c: str) -> Image.Image:
        return Image.fromarray(np.uint8(self.get_char_array(c) * 255))

    @property
    def n_bytes(self):
        return ((self.width * self.height) // 8) + (self.width * self.height % 8 > 0)

    @property
    def end_offset(self):
        return (8 - self.width * self.height % 8) * (self.width * self.height % 8 > 0)

    def char_from_font(self, c: str, font: ImageFont.ImageFont):
        width, height = font.getsize(c)
        assert self.height == height

        if width == 0:
            # Character not in the font, make blank.
            return self.add_missing_char(c)

        assert (
            self.width == width
        ), f"The font probably is not monospace [ char: {c}, expected_width = {self.width}, width = {width}"
        img = to_image(c, font)
        array = np.asarray(img.getdata(0), dtype=bool).reshape(
            (self.height, self.width)
        )

        seek: int = (ord(c) - 32) * self.n_bytes + 2

        b_seek: int = 0

        for x in range(self.width):
            for y in range(self.height):
                if array[y, x]:
                    self._bytes[seek] |= 0b00000001 << b_seek

                b_seek += 1
                if b_seek == 8:
                    b_seek = 0
                    seek += 1

    def add_missing_char(self, c: str):
        array = np.zeros((self.height, self.width), dtype=bool)

        array[:, 0] = True
        array[:, -1] = True
        array[0, :] = True
        array[-1, :] = True

        seek: int = (ord(c) - 32) * self.n_bytes + 2

        b_seek: int = 0

        for x in range(self.width):
            for y in range(self.height):
                if array[y, x]:
                    self._bytes[seek] |= 0b00000001 << b_seek

                b_seek += 1
                if b_seek == 8:
                    b_seek = 0
                    seek += 1

    @classmethod
    def load_header(cls, path: Path, extended: bool = False) -> "CustomFont":
        command = "gcc -E"
        if extended:
            command += " -D SSD1306_ASCII_FULL"
        header = subprocess.run(
            [*command.split(" "), path], stdout=subprocess.PIPE
        ).stdout.decode("utf-8")

        # Process the header
        header = header[header.index("[] = {") + 5 :]

        header = header.replace("\n\n", ",\n\n")

        header = header[: header.rfind(";")]
        header = header.replace("{", "").replace("}", "").replace(",", " ").replace("0x", "").replace("// font width, height", "").replace('\n', ' ')

        font_data = bytes(map(lambda n: int(n, base=16),header.split()))
        result = cls(
            font_data[0],
            font_data[1],
            extended=extended,
        )
        result._bytes = font_data
        return result



    @classmethod
    def from_font(
        cls, font: ImageFont.ImageFont, extended: bool = True
    ) -> "CustomFont":
        width, height = font.getsize(" ")
        cfont = cls(width, height, extended)
        end = 256 if extended else 127

        cfont._bytes = bytearray([0] * ((end - 32) * cfont.n_bytes + 2))
        cfont._bytes[0] = width
        cfont._bytes[1] = height
        for idx in range(32, end):
            cfont.char_from_font(chr(idx), font)

        return cfont

    def generate_font_data(self, extended: bool = True) -> str:
        drop_start = "\n   " if extended else ""
        result = f"    0x{self.width:x},{drop_start} 0x{self.height:x}, // font width, height"

        end = 256 if extended else 127
        for idx in range(32, end):
            result += "\n\n" + "\n".join(
                [f"    0x{val:x}," for val in self.chars(idx)]
            )
        return result

    def create_header(self, font_name: str) -> str:
        header_define = f"SSD1306_{self.width}X{self.height}_{font_name.upper()}_H"

        font_var_name = (
            f"const unsigned char {font_name.lower()}_{self.width}x{self.height}[] = {{"
        )

        return f"""#ifndef {header_define}
#define {header_define}

#ifndef SSD1306_ASCII_FULL
{font_var_name}
{self.generate_font_data(extended=False)[:-1]}}};

#else
{font_var_name}
{self.generate_font_data(extended=True)}
}};

#endif // SSD1306_ASCII_FULL
#endif // {header_define}
"""
