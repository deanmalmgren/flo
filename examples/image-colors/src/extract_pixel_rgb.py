"""read the pixel-by-pixel RGB of an image and output the rgb values
as a function of space
"""

import sys

from PIL import Image
filename = sys.argv[1]
print >> sys.stderr, "extracting RGB values from", filename
image = Image.open(filename)
pix = image.load()
width, height = image.size
for x in range(width):
    for y in range(height):

        # black/white images just store a single value. cast as rgb
        # here for convenience downstream
        val = pix[x, y]
        if isinstance(val, int):
            print filename, x, y, val, val, val
        else:
            print filename, x, y, ' '.join(map(str, val))
