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

        # black/white images just store a single value. cast as rgb
        # here for convenience downstream
        val = pix[x, y]
        if isinstance(val, int):
            print x, y, val, val, val
        else:
            print x, y, ' '.join(map(str, val))
