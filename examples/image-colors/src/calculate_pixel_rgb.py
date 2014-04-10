"""read the pixel-by-pixel RGB of an image and output the rgb values
as a function of space
"""

import sys

from PIL import Image
image = Image.open(sys.argv[1])
pix = image.load()
width, height = image.size
for x in range(width):
    for y in range(height):
        r, g, b = pix[x, y]
        print x, y, r, g, b
