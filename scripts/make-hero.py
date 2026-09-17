#!/usr/bin/env python3
"""Human² hero image: the New Adam with wordmark and tagline (2812x1674).

Made for wide banner and cover placements. Four combinations of darkening x vignette, all with the baked text
(Human² wordmark + SF Pro Semibold headline, soft website-style shadows):
  1. bright
  2. bright + vignette
  3. slightly darkened (brightness 0.75)
  4. slightly darkened + vignette

The wordmark is the official artwork (wordmark/*-inverted.png) used as a
mask, never re-typeset, so it always matches the brand files.

Ported from the waveful-presentations repo, where the same image
carried a "WAVEFUL" eyebrow.

Requires Pillow and macOS (SF Pro is read from /System/Library/Fonts).
Source: hero/source/the-new-adam.jpg
Output: hero/human2-hero-{bright,dark}[-vignette].jpg
"""
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
import os

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

SRC = 'hero/source/the-new-adam.jpg'
WORDMARK = 'wordmark/human2-wordmark-1x1-3168x3168-inverted.png'
OUT_DIR = 'hero'
os.makedirs(OUT_DIR, exist_ok=True)

base = Image.open(SRC).convert('RGB')
# The fingertip touch sits at x=1406 of 3000 (46.9%). Cut the right side
# so the touch lands exactly at the horizontal center: width = 2 * 1406.
TOUCH_X = 1406
base = base.crop((0, 0, 2 * TOUCH_X, base.size[1]))
W, H = base.size  # 2812 x 1674
S = H / 720.0

sf = ImageFont.truetype('/System/Library/Fonts/SFNS.ttf', int(52 * S))
sf.set_variation_by_name('Semibold')

# Wordmark artwork -> alpha mask: white ink on black, ink peaks at 236,
# so stretch levels to a clean 0..255 and trim to the ink bounds.
_wm = Image.open(WORDMARK).convert('L').point(lambda v: min(255, max(0, (v - 12) * 255 // 212)))
_wm = _wm.crop(_wm.getbbox())
WORDMARK_H = 0.040 * H  # ink height, top of the H to the baseline
wordmark = _wm.resize((round(_wm.width * WORDMARK_H / _wm.height), round(WORDMARK_H)), Image.LANCZOS)


def vignette(im):
    mask = Image.new('L', (W, H), 255)
    ImageDraw.Draw(mask).ellipse((0.02 * W, 0.00 * H, 0.98 * W, 1.00 * H), fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(260))
    return Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), im, mask)


def bake(im, layer, fill, shadow_alpha, shadow_blur_css, shadow_dy_css):
    """Paint a full-canvas L mask onto im with a CSS-like soft drop shadow."""
    shadow = layer.filter(ImageFilter.GaussianBlur(shadow_blur_css / 2 * S))
    shadow = shadow.point(lambda v: int(v * shadow_alpha))
    im.paste(Image.new('RGB', (W, H), (0, 0, 0)), (0, int(shadow_dy_css * S)), shadow)
    im.paste(Image.new('RGB', (W, H), fill), (0, 0), layer)
    return im


def text_layer(text, font, top_y):
    layer = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(layer)
    d.text((W / 2 - d.textlength(text, font=font) / 2, top_y), text, font=font, fill=255)
    return layer


def wordmark_layer(bottom_y):
    layer = Image.new('L', (W, H), 0)
    layer.paste(wordmark, (round(W / 2 - wordmark.width / 2), round(bottom_y - wordmark.height)))
    return layer


def add_text(im):
    # wide-crop safe: everything stays in a tight band around the hands
    # without touching them (hands span ~0.38-0.47 H)
    bake(im, wordmark_layer(0.380 * H), (240, 240, 240), 0.60, 10, 2)
    bake(im, text_layer('Merging Humans and Machines', sf, 0.50 * H), (255, 255, 255), 0.55, 12, 2)
    return im


variants = {
    'human2-hero-bright.jpg': lambda: add_text(base.copy()),
    'human2-hero-bright-vignette.jpg': lambda: add_text(vignette(base.copy())),
    'human2-hero-dark.jpg': lambda: add_text(ImageEnhance.Brightness(base).enhance(0.75)),
    'human2-hero-dark-vignette.jpg': lambda: add_text(vignette(ImageEnhance.Brightness(base).enhance(0.75))),
}
for fname, make in variants.items():
    make().save(os.path.join(OUT_DIR, fname), quality=92)
    print(fname)
