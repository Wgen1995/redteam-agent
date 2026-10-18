# 出处:人工构造(硬负例:固定输入图片缩略)
from PIL import Image
im = Image.open(LOGO)
im.thumbnail((64, 64))
