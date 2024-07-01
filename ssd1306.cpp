#include "ssd1306.h"
#include <array>

namespace pico_ssd1306 {
    SSD1306::SSD1306(i2c_inst *i2CInst, uint16_t Address, Size size) {
        // Set class instanced variables
        this->i2CInst = i2CInst;
        this->address = Address;
        this->size = size;

        this->width = 128;

        if (size == Size::W128xH32) {
            this->height = 32;
        } else {
            this->height = 64;
        }

        // display is not inverted by default
        this->inverted = false;

        // this is a list of setup commands for the display
        uint8_t setup[] = {
                SSD1306_DISPLAY_OFF,
                SSD1306_LOWCOLUMN,
                SSD1306_HIGHCOLUMN,
                SSD1306_STARTLINE,

                SSD1306_MEMORYMODE,
                SSD1306_MEMORYMODE_HORZONTAL,

                SSD1306_CONTRAST,
                0xFF,

                SSD1306_INVERTED_OFF,

                SSD1306_MULTIPLEX,
                63,

                SSD1306_DISPLAYOFFSET,
                0x00,

                SSD1306_DISPLAYCLOCKDIV,
                0x80,

                SSD1306_PRECHARGE,
                0x22,

                SSD1306_COMPINS,
                0x12,

                SSD1306_VCOMDETECT,
                0x40,

                SSD1306_CHARGEPUMP,
                0x14,

                SSD1306_DISPLAYALL_ON_RESUME,
                SSD1306_DISPLAY_ON
        };

        // send each one of the setup commands
        for (uint8_t &command: setup) {
            this->cmd(command);
        }

        // clear the buffer and send it to the display
        // if not done display shows garbage data
        this->clear();
        this->sendBuffer();

    }

    void SSD1306::setPixel(int16_t x, int16_t y, WriteMode mode) {
        // return if position out of bounds
        if ((x < 0) || (x >= this->width) || (y < 0) || (y >= this->height)) return;

        // byte to be used for buffer operation
        uint8_t byte;

        // display with 32 px height requires doubling of set bits, reason to this is explained in readme
        // this shifts 1 to byte based on y coordinate
        // remember that buffer is a one dimension array, so we have to calculate offset from coordinates
        if (size == Size::W128xH32) {
            y = (y << 1) + 1;
            byte = 1 << (y & 7);
            char byte_offset = byte >> 1;
            byte = byte | byte_offset;
        } else {
            byte = 1 << (y & 7);
        }

        // check the write mode and manipulate the frame buffer
        if (mode == WriteMode::ADD) {
            this->frameBuffer.byteOR(x + (y / 8) * this->width, byte);
        } else if (mode == WriteMode::SUBTRACT) {
            this->frameBuffer.byteAND(x + (y / 8) * this->width, ~byte);
        } else if (mode == WriteMode::INVERT) {
            this->frameBuffer.byteXOR(x + (y / 8) * this->width, byte);
        }


    }
            

    void SSD1306::sendBuffer() {
            if(! this->postpone_system) {
        this->cmd(SSD1306_PAGEADDR); //Set page address from min to max
        this->cmd(0x00);
        this->cmd(0x07);
        this->cmd(SSD1306_COLUMNADDR); //Set column address from min to max
        this->cmd(0x00);
        this->cmd(127);

            // create a temporary buffer of size of buffer plus 1 byte for startline command aka 0x40
            unsigned char data[FRAMEBUFFER_SIZE + 1];

            data[0] = SSD1306_STARTLINE;

            // copy framebuffer to temporary buffer
            memcpy(data + 1, frameBuffer.get(), FRAMEBUFFER_SIZE);

        // send data to device
        // very long time, as it takes ~100ms to send 1025 bytes
    
        int i2c_sdk_call_return_value = i2c_write_blocking_until(
            this->i2CInst, this->address, data, FRAMEBUFFER_SIZE + 1, false,
            make_timeout_time_ms(200));
        if (i2c_sdk_call_return_value != FRAMEBUFFER_SIZE + 1) {
            this->x = i2c_sdk_call_return_value;
            this->enabled = false;
        }
        } else {
            this->postponed_write = true;
            this->postponed_write_count = 0;
            this->cmd(0x21);
            this->cmd(0);// await self.write_cmd_async(xpos0)
            this->cmd(127);// await self.write_cmd_async(xpos1)
            this->cmd(0x22);// await self.write_cmd_async(0x22)  # SET_PAGE_ADDR)
            this->cmd(0);// await self.write_cmd_async(0)
            this->cmd(7);// await self.write_cmd_async(self.pages - 1)
        }
    }

    void SSD1306::clear() {
        this->frameBuffer.clear();
    }

    void SSD1306::setOrientation(bool orientation) {
        // remap columns and rows scan direction, effectively flipping the image on display
        if (orientation) {
            this->cmd(SSD1306_CLUMN_REMAP_OFF);
            this->cmd(SSD1306_COM_REMAP_OFF);
        } else {
            this->cmd(SSD1306_CLUMN_REMAP_ON);
            this->cmd(SSD1306_COM_REMAP_ON);
        }
    }

    void
    SSD1306::addBitmapImage(int16_t anchorX, int16_t anchorY, uint8_t image_width, uint8_t image_height,
                            uint8_t *image,
                            WriteMode mode) {
        uint8_t byte;
        // goes over every single bit in image and sets pixel data on its coordinates
        for (uint8_t y = 0; y < image_height; y++) {
            for (uint8_t x = 0; x < image_width / 8; x++) {
                byte = image[y * (image_width / 8) + x];
                for (uint8_t z = 0; z < 8; z++) {
                    if ((byte >> (7 - z)) & 1) {
                        this->setPixel(x * 8 + z + anchorX, y + anchorY, mode);
                    }
                }
            }
        }

    }

    void SSD1306::invertDisplay() {
        this->cmd(SSD1306_INVERTED_OFF | !this->inverted);
        inverted = !inverted;
    }

    void SSD1306::cmd(unsigned char command) {
        // 0x00 is a byte indicating to ssd1306 that a command is being sent
        uint8_t data[2] = {0x00, command};
  int i2c_sdk_call_return_value = i2c_write_blocking_until(
      this->i2CInst, this->address, data, 2, false, make_timeout_time_ms(10));
  if (i2c_sdk_call_return_value != 2) {
    this->enabled = false;
  }
}

    void SSD1306::setContrast(unsigned char contrast) {
        this->cmd(SSD1306_CONTRAST);
        this->cmd(contrast);
    }

    void SSD1306::setBuffer(unsigned char * buffer) {
        this->frameBuffer.setBuffer(buffer);
    }

    void SSD1306::turnOff() {
        this->cmd(SSD1306_DISPLAY_OFF);
    }

    void SSD1306::turnOn() {
        this->cmd(SSD1306_DISPLAY_ON);
    }
    bool SSD1306::sendLine(int line) {
        std::array<uint8_t, 17> data;
        data[0] = 0x40;
        for (int i = 0; i < 16; i++) {
            data[i+1] = this->frameBuffer.get()[line * 16 + i];
        }
        int i2c_sdk_call_return_value = i2c_write_blocking_until(
            this->i2CInst, this->address, data.data(), 17, false,
            make_timeout_time_ms(10));
        if (i2c_sdk_call_return_value != 17) {
            this->x = i2c_sdk_call_return_value;
            this->enabled = false;
            return false;
        }
        return true;
    }

    // send a small package each time instead of blocking the whole mcu for 100ms
    bool SSD1306::postWrite() {
        if (this->postponed_write) {
            // send one line
            this->sendLine(this->postponed_write_count);
            this->postponed_write_count++;
            if (this->postponed_write_count == 64) {
                // this->sendBuffer();
                this->postponed_write = false;
                this->postponed_write_count = 0;
            }
        }
        return this->postponed_write;
    }

}
