#!/usr/bin/env python3
"""
Compress images in static/images to reduce size and improve site speed.
Uses Pillow: PNG optimized, JPEG/WebP with quality 82–85.
Only overwrites when the compressed file is smaller than the original.
Run from project root: python scripts/compress_images.py
"""
import io
import os
import sys
from typing import Tuple

# Allow running from project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
IMAGES_DIR = os.path.join(PROJECT_ROOT, 'static', 'images')

try:
    from PIL import Image
except ImportError:
    print("Install Pillow: pip install Pillow")
    sys.exit(1)


def compress_image(path: str, quality_jpeg: int = 82, quality_webp: int = 82) -> Tuple[bool, int, int]:
    """Compress one image. Overwrites only if smaller. Returns (replaced, orig_size, new_size)."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in ('.png', '.jpg', '.jpeg', '.webp', '.gif'):
        return False, 0, 0
    try:
        orig_size = os.path.getsize(path)
    except OSError:
        return False, 0, 0
    try:
        img = Image.open(path).copy()
        if img.mode in ('P', 'PA'):
            img = img.convert('RGBA')
        if ext in ('.jpg', '.jpeg') and img.mode != 'RGB':
            img = img.convert('RGB')
    except Exception as e:
        print(f"  Skip {os.path.basename(path)}: {e}")
        return False, orig_size, orig_size

    buf = io.BytesIO()
    if ext in ('.jpg', '.jpeg'):
        img.save(buf, 'JPEG', quality=quality_jpeg, optimize=True)
    elif ext == '.png':
        img.save(buf, 'PNG', optimize=True)
    elif ext == '.webp':
        img.save(buf, 'WEBP', quality=quality_webp, method=6)
    elif ext == '.gif':
        img.save(buf, 'GIF', optimize=True)
    else:
        return False, orig_size, orig_size

    new_size = buf.tell()
    if new_size < orig_size:
        with open(path, 'wb') as f:
            f.write(buf.getvalue())
        pct = (1 - new_size / orig_size) * 100
        print(f"  {os.path.basename(path)}: {orig_size // 1024} KB -> {new_size // 1024} KB ({pct:.0f}% smaller)")
        return True, orig_size, new_size
    else:
        print(f"  {os.path.basename(path)}: {orig_size // 1024} KB (unchanged, already optimal)")
        return False, orig_size, orig_size


def main():
    if not os.path.isdir(IMAGES_DIR):
        print(f"Images directory not found: {IMAGES_DIR}")
        sys.exit(0)
    print(f"Compressing images in {IMAGES_DIR} ...")
    total_orig = 0
    total_new = 0
    for name in sorted(os.listdir(IMAGES_DIR)):
        path = os.path.join(IMAGES_DIR, name)
        if not os.path.isfile(path):
            continue
        replaced, s_orig, s_new = compress_image(path)
        total_orig += s_orig
        total_new += s_new
    if total_orig:
        pct = (1 - total_new / total_orig) * 100
        print(f"Total: {total_orig // 1024} KB -> {total_new // 1024} KB ({pct:.0f}% smaller)")
    print("Done.")


if __name__ == '__main__':
    main()
