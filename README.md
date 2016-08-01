# Combining Layers to Isolate Pixels (CLIP)
A program that can recreate a partially-semitransparent image, given copies of it with a black background and a white background.

Version 1.0

Copyright (C) 2016  RoadrunnerWMC

Begun 1/29/14, heavily improved 7/31/16.


## Overview

![Example](https://raw.githubusercontent.com/RoadrunnerWMC/clip/readme-example.png)

CLIP was written for the purpose of creating images of objects in video games that preserve antialiasing and semitransparency. Video games can't be made to render with literally transparent backgrounds, but one can often make the background of a scene to be black or white. Taking two otherwise-identical screenshots with a black background and a white background allows CLIP to calculate what the scene would look like if the background was actually transparent. There are probably other use cases for this, too.

The program could conceivably be generalized to accept backgrounds of other colors, and even image backgrounds (in which case, the backgrounds themselves would also need to be inputs to the program). This is not implemented for several reasons:

- I tried a while ago and couldn't make it work.
- Obtaining black-background and white-background images is feasible for all of my personal use cases.
- Most of the program (both the UI layer and the backend) would need to be replaced.
    - I do happen to already have an older version of the program with a UI that supports all of those generalizations and more; however, it is quite a bit more complicated to use, and requires several more clicks for the black/white backgrounds case. It also lacks many general code updates I've made since then.)
- The output would likely not look as good as it does for input with fully-black and fully-white backgrounds because the contrast between background colors would not be as great.
- Furthermore, for image backgrounds, the contrast between background colors would vary in different regions, which would likely cause artifacts in the output.

Derivations of the formulas used in the program are included in source code comments in algorithm.py.


## Running the program

Run clip.py with Python 3.5 or newer. PyQt5 needs to be installed for the copy of Python you're using, as well.

CLIP's UI is intuitive enough that it should need no explanation. One word of caution, though -- you need to make sure that the image with the black background and the image with the white background otherwise line up *perfectly*. A single-pixel position difference can wreck everything.


## Licensing

clip.py, which contains all of the UI code, is licensed under the GNU GPL v3 (Qt and PyQt are licensed as such, and GPL has copyleft). algorithm.py, which contains the actual color math, is instead licensed under the MIT license, so you can use that part of the source code without copyleft restrictions.
