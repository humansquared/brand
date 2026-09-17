#!/usr/bin/env python3
"""Human² hero image: the New Adam with wordmark and tagline (2812x1674).

Made for wide banner and cover placements. Two layouts:
  centred  the fingertip touch and the text sit at the exact centre
  offset   touch and text sit at 61% of the width, zoomed in 1.22x from
           the left edge, so an avatar or logo overlapping the lower left
           of a profile banner does not cover the headline

Each layout comes in four treatments of darkening x vignette, all with
the baked text (Human² wordmark + SF Pro Semibold headline, soft
website-style shadows):
  bright, bright-vignette, dark (brightness 0.75), dark-vignette

The wordmark is the official artwork (wordmark/*-inverted.png) used as a
mask, never re-typeset, so it always matches the brand files.

Ported from the waveful-presentations repo, where the same image
carried a "WAVEFUL" eyebrow.

Requires Pillow and macOS (SF Pro is read from /System/Library/Fonts).
Source: hero/source/the-new-adam-5504x3072.jpg (JPEG of the landscape
        master kept in the the-new-adam repo)
Output: hero/human2-hero-[offset-]{bright,dark}[-vignette].jpg
"""
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
import os

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

SRC = 'hero/source/the-new-adam-5504x3072.jpg'
WORDMARK = 'wordmark/human2-wordmark-1x1-3168x3168-inverted.png'
OUT_DIR = 'hero'
os.makedirs(OUT_DIR, exist_ok=True)

Image.MAX_IMAGE_PIXELS = None
master = Image.open(SRC).convert('RGB')
MW, MH = master.size
TOUCH_X = 0.4687 * MW  # the fingertip touch
ANCHOR_Y = 0.44        # zooming keeps this height fixed, so the hands stay under the text
W, H = 2812, 1674
S = H / 720.0

LAYOUTS = {'': 0.50, 'offset-': 0.61}  # file name infix -> touch position, fraction of the width

sf = ImageFont.truetype('/System/Library/Fonts/SFNS.ttf', int(52 * S))
sf.set_variation_by_name('Semibold')

# Wordmark artwork -> alpha mask: white ink on black, ink peaks at 236,
# so stretch levels to a clean 0..255 and trim to the ink bounds.
_wm = Image.open(WORDMARK).convert('L').point(lambda v: min(255, max(0, (v - 12) * 255 // 212)))
_wm = _wm.crop(_wm.getbbox())
WORDMARK_H = 0.027 * H  # ink height, top of the H to the baseline
wordmark = _wm.resize((round(_wm.width * WORDMARK_H / _wm.height), round(WORDMARK_H)), Image.LANCZOS)


def ground(p):
    """Crop the master from its left edge so the touch lands at fraction p of the width.

    p = 0.50 uses the full height and cuts only the right side; a larger p
    narrows the crop, which zooms in.
    """
    cw = TOUCH_X / p
    ch = cw * H / W
    y0 = ANCHOR_Y * (MH - ch)
    return master.crop((0, round(y0), round(cw), round(y0 + ch))).resize((W, H), Image.LANCZOS)


def vignette(im):
    mask = Image.new('L', (W, H), 255)
    ImageDraw.Draw(mask).ellipse((0.02 * W, 0.00 * H, 0.98 * W, 1.00 * H), fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(260))
    return Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), im, mask)


def darken(im):
    return ImageEnhance.Brightness(im).enhance(0.75)


def bake(im, layer, fill, shadow_alpha, shadow_blur_css, shadow_dy_css):
    """Paint a full-canvas L mask onto im with a CSS-like soft drop shadow."""
    shadow = layer.filter(ImageFilter.GaussianBlur(shadow_blur_css / 2 * S))
    shadow = shadow.point(lambda v: int(v * shadow_alpha))
    im.paste(Image.new('RGB', (W, H), (0, 0, 0)), (0, int(shadow_dy_css * S)), shadow)
    im.paste(Image.new('RGB', (W, H), fill), (0, 0), layer)
    return im


def text_layer(text, font, center_x, top_y):
    layer = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(layer)
    d.text((center_x - d.textlength(text, font=font) / 2, top_y), text, font=font, fill=255)
    return layer


def wordmark_layer(center_x, bottom_y):
    layer = Image.new('L', (W, H), 0)
    layer.paste(wordmark, (round(center_x - wordmark.width / 2), round(bottom_y - wordmark.height)))
    return layer


def add_text(im, center_x):
    # wide-crop safe: everything stays in a tight band around the hands
    # without touching them (hands span ~0.38-0.47 H)
    bake(im, wordmark_layer(center_x, 0.380 * H), (240, 240, 240), 0.60, 10, 2)
    bake(im, text_layer('Merging Humans and Machines', sf, center_x, 0.50 * H), (255, 255, 255), 0.55, 12, 2)
    return im


TREATMENTS = {
    'bright': lambda im: im,
    'bright-vignette': vignette,
    'dark': darken,
    'dark-vignette': lambda im: vignette(darken(im)),
}
for infix, p in LAYOUTS.items():
    base = ground(p)
    for name, treat in TREATMENTS.items():
        fname = f'human2-hero-{infix}{name}.jpg'
        add_text(treat(base.copy()), p * W).save(os.path.join(OUT_DIR, fname), quality=92)
        print(fname)
