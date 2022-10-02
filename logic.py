from io import BytesIO

import win32clipboard as clip
import win32con
from PIL import Image, ImageOps


def invert_image(image: Image):
    if image.mode == "RGBA":
        r, g, b, a = image.split()
        rgb_image = Image.merge("RGB", (r, g, b))
        inverted_image = ImageOps.invert(rgb_image)
        r2, g2, b2 = inverted_image.split()
        return Image.merge("RGBA", (r2, g2, b2, a))
    else:
        return ImageOps.invert(image)


def invert_image_with_blend(image: Image, invert_power: int):
    inverted_image = invert_image(image)
    blended_image = Image.blend(image, inverted_image, invert_power / 100)
    return blended_image


def to_clipboard(image: Image):
    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    clip.OpenClipboard()
    clip.EmptyClipboard()
    clip.SetClipboardData(win32con.CF_DIB, data)
    clip.CloseClipboard()
