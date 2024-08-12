import hashlib
from PIL import Image
import math


def hash_code(s, salt='nemo'):
    md5 = hashlib.md5()
    s += salt
    md5.update(s.encode('utf-8'))
    return md5.hexdigest()


def is_grayscale(image_path):
    image = Image.open(image_path)
    grayscale_image = image.convert("L")
    return image.mode == "L"

def image_to_binary(image_path):
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            binary_data = ''.join(format(byte, '08b') for byte in image_data)
            with open('example2.txt', 'w') as f:
                f.writelines(binary_data)
            return 'example2.txt'
    except FileNotFoundError:
        return "Error: File not found."


def toRGB(path):
    with open(path, 'rb') as file:
        binary = file.read()
    binary = str(binary)
    binary = binary.replace(" ", "").replace("b'", "").replace("'", "")  # 去掉空格和其他非二进制字符

    for i in range(0, len(binary), 24):
        if i + 24 > len(binary):
            zero_len = i + 24 - len(binary)
            width = zero_len + len(binary)
            binary = binary.ljust(width, "0")

    binary = [binary[i:i + 8] for i in range(0, len(binary), 8)]  # 按照字节分割

    rgb = []
    for i in range(0, len(binary), 3):
        r = int(binary[i], 2)  # 将二进制转换为十进制
        g = int(binary[i + 1], 2)
        b = int(binary[i + 2], 2)
        rgb.append((r, g, b))  # 将 RGB 值添加到列表中
    side = int(math.sqrt(len(rgb)))
    if side ** 2 < len(rgb):
        side += 1
        rgb.extend([(0, 0, 0)] * (side ** 2 - len(rgb)))
    image = []
    for i in range(0, len(rgb), side):
        row = rgb[i:i + side]
        image.append(row)
    img = Image.new("RGB", (side, side))
    img.putdata([rgb for row in image for rgb in row])  # 将 RGB 值填充到图像中
    img_path = "rgb.png"
    img.save(img_path)
    return img_path
