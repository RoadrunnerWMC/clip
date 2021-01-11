# This file, part of CLIP by RoadrunnerWMC, contains the actual
# algorithm that does the calculations. It has been placed in its own
# source code file so that it can be released under a different license
# than the UI.

# This file (algorithm.py) is licensed under the MIT license.
# clip.py is instead licensed under the GNU GPL v3.

# The following license applies only to this single source code file
# (algorithm.py):

# MIT License
#
# Copyright (c) 2016 RoadrunnerWMC
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import threading


class AbstractAlgorithm(threading.Thread):
    """
    Class that represents the transparent-color-choosing algorithm in an
    abstract form. You need to override at least two of its functions to
    make a concrete implementation.
    """
    width = height = 0
    canceled = False

    def __init__(self):
        super().__init__(name='Algorithm')

    def cancel(self):
        """
        Quit immediately
        """
        self.canceled = True
        self.finishedHandler(False)

    def run(self):
        """
        Run the algorithm, calling `rowCompletedHandler` and
        `finishedHandler` when applicable
        """

        # Iterate through the pixels
        for y in range(self.height):
            for x in range(self.width):
                if self.canceled: return

                # Get relevant colors
                blackCol, whiteCol = self.getColors(x, y)

                # Get the actual color (bottleneck)
                finalColor = self._calculateOverlayColor(blackCol, whiteCol)

                # Paint it
                self.putColor(*finalColor, x=x, y=y)

            # Call a function with the current percentage as an argument
            self.rowCompletedHandler(100 * ((y * 1.0) / self.height))

        # Finish up
        self.finishedHandler(True)

    def _calculateOverlayColor(self, blackCol, whiteCol):
        """
        Calculate the overlay color (r, g, b, a) based on the
        black-background and white-background observed colors given
        (each of which is (r, g, b))
        """

        # Here's the underlying algebra.
        #
        #     In general, for a single color channel:
        #
        #         a: opacity (0 to 1)
        #         b: background color (0 to 255)
        #         c: observed color (0 to 255)
        #         t: true color (0 to 255)
        #
        #         c = b + a (t - b)
        #
        #     Apply the original formula to the black-BG and white-BG
        #         observed colors (again, only a single channel):
        #
        #         c₁: observed black color (0 to 255)
        #         c₂: observed white color (0 to 255)
        #
        #         Black (b = 0):
        #             c₁ = 0 + a (t - 0)
        #             c₁ = a t
        #
        #         White (b = 255):
        #             c₂ = 255 + a (t - 255)
        #             c₂ = 255 + a t - 255 a
        #             c₂ = 255 (1 - a) + a t
        #
        #     Now we can combine those equations to solve for a:
        #         c₂ = 255 (1 - a) + c₁
        #         c₂ - c₁ = 255 (1 - a)
        #         1 - ((c₂ - c₁) / 255) = a
        #         a = 1 - ((c₂ - c₁) / 255)
        #
        #     In an actual implementation, we can just pick a channel
        #         and apply that formula to it to calculate the opacity.
        #         Picking the one with the most contrast is a good idea.
        #
        #     Now that we have a, we can use the "c₁ = a t" equation to
        #     find t:
        #         t = c₁ / a
        #
        #     Do that last step for all three channels (r, g, b), using
        #         the same opacity value we calculated earlier. Now we
        #         have found all four channels (r, g, b, a) of the true
        #         color.

        (bR, bG, bB), (wR, wG, wB) = blackCol, whiteCol

        # We can short-circuit the common cases of fully-transparent and
        # fully-opaque.

        # Fully transparent
        if (bR == bG == bB == 0) and (wR == wG == wB == 255):
            return 0, 0, 0, 0

        # Fully opaque
        if (bR == wR) and (bG == wG) and (bB == wB):
            return bR, bG, bB, 255

        # If we've reached here, it's semitransparent. Do the actual
        # calculation.

        # Find opacity
        a = 1 - (max(wR - bR, wG - bG, wB - bB) / 255)
        a = min(a, 1)
        if a <= 0:
            return 0, 0, 0, 0

        # Find r, g and b (and make a go from 0 to 255)
        r = min(max(bR / a, 0), 255)
        g = min(max(bG / a, 0), 255)
        b = min(max(bB / a, 0), 255)
        a *= 255

        # Return the final color
        return int(r), int(g), int(b), int(a)

    def getColor(self, x, y):
        """
        Get black/white pixel colors from a certain position.
        Implement this in subclasses.
        """
        raise NotImplementedError('getColor() must be implemented in'
            ' subclasses.')

    def putColor(self, r, g, b, a, x, y):
        """
        Set a pixel in the output image to the color (r, g, b, a).
        Implement this in subclasses.
        """
        raise NotImplementedError('putColor() must be implemented in'
            ' subclasses.')

    def rowCompletedHandler(self, pct):
        """
        Placeholder handler function for a row being completed.
        """
        pass

    def finishedHandler(self, success):
        """
        Placeholder handler function for the algorithm being completed
        or canceled. `success` will be `False` if the algorithm was
        canceled prematurely by the user, and `True` otherwise.
        """
        pass
