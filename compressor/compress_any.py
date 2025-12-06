import sys
import os
import argparse
import io
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import json

from PIL import Image
import fitz  # PyMuPDF

from .utils import ensure_dir, parse_size_str, readable_size, timestamp_name, parse_dimensions

# Supported formats
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
PDF_EXTS = {'.pdf'}

def get_target_bytes(target_key: str) -> int:
    return parse_size_str(target_key)

def compress_image_data(img: Image.Image, fmt: str, target_bytes: int, target_dims: Tuple[int, int] = None) -> Tuple[bytes, str]:
    """
    Compress PIL Image to target_bytes.
    If target_dims (w, h) provided, resize to that first.
    Returns (compressed_bytes, format_used).
    """
    # Strip EXIF by creating new image
    data = list(img.getdata())
    image_without_exif = Image.new(img.mode, img.size)
    image_without_exif.putdata(data)
    
    # Convert to RGB if needed (e.g. for JPEG)
    if img.mode in ('RGBA', 'P'):
        rgb_im = img.convert('RGB')
    else:
        rgb_im = img

    # Resize to specific dimensions if requested
    if target_dims:
        rgb_im = rgb_im.resize(target_dims, Image.Resampling.LANCZOS)

    # Strategy: 
    # 1. Try WebP (if fmt allows or generic) - usually smaller.
    # 2. Try JPEG.
    # 3. Resize if needed.
    
    candidates = []
    
    # Helper to try compression at specific quality
    def try_compress(image, format_name, quality):
        buf = io.BytesIO()
        try:
            image.save(buf, format=format_name, quality=quality, optimize=True)
        except Exception:
            return None
        return buf.getvalue()

    # Formats to try
    formats_to_try = []
    if fmt.lower() in ['webp', 'auto']:
        formats_to_try.append('WEBP')
    if fmt.lower() in ['jpeg', 'jpg', 'auto']:
        formats_to_try.append('JPEG')
    
    # If input was PNG and we want to keep it PNG? 
    # Prompt says: "Convert PNG/WebP to RGB JPEG when it reduces size."
    # So we prefer lossy formats for size.
    
    # Binary search for quality
    def fit_quality(image, format_name):
        low, high = 5, 100
        best = None
        while low <= high:
            mid = (low + high) // 2
            blob = try_compress(image, format_name, mid)
            if blob:
                if len(blob) <= target_bytes:
                    best = blob
                    low = mid + 1 # Try for better quality
                else:
                    high = mid - 1
        return best

    # Resize loop
    current_img = rgb_im
    scale_step = 0.9
    min_dim = 100
    
    for _ in range(10): # Max 10 resize steps
        for f in formats_to_try:
            res = fit_quality(current_img, f)
            if res:
                candidates.append((len(res), res, f))
        
        if candidates:
            # Sort by size (descending) but must be <= target (already filtered)
            # Actually we want the highest quality that fits. 
            # Since we binary searched for max quality, the first one that fit is good.
            # But between formats? WebP usually looks better at same size.
            # Let's pick the one that is largest bytes (closest to target) as proxy for quality?
            # Or just pick the first one found?
            # Let's pick the one with largest size <= target_bytes
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1], candidates[0][2]
        
        # If no fit, resize
        w, h = current_img.size
        if w < min_dim or h < min_dim:
            break
        new_size = (int(w * scale_step), int(h * scale_step))
        current_img = current_img.resize(new_size, Image.Resampling.LANCZOS)
        
    # If we failed to meet target even after resize, return best effort (smallest we got)
    # We need to re-run compression on smallest image with lowest quality
    fallback_blob = try_compress(current_img, formats_to_try[-1], 5)
    return fallback_blob, formats_to_try[-1]


def compress_pdf(input_path: Path, target_bytes: int) -> Tuple[bytes, str]:
    """
    Compress PDF by rasterizing pages and compressing them.
    """
    doc = fitz.open(input_path)
    page_count = len(doc)
    if page_count == 0:
        return b'', 'PDF'
        
    # Budget per page (naive)
    # Reserve 10% for overhead
    budget_per_page = int((target_bytes * 0.9) / page_count)
    if budget_per_page < 5000: budget_per_page = 5000 # Min 5KB per page
    
    out_pdf = fitz.open()
    
    for page in doc:
        pix = page.get_pixmap(dpi=150) # Moderate DPI
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Compress this page image
        compressed_page_bytes, fmt = compress_image_data(img, 'JPEG', budget_per_page)
        
        # Create new PDF page from compressed image
        img_page = out_pdf.new_page(width=page.rect.width, height=page.rect.height)
        img_page.insert_image(page.rect, stream=compressed_page_bytes)
        
    out_bytes = out_pdf.tobytes()
    
    # If total is still too big, we could try again with lower DPI, but for now return best effort
    return out_bytes, 'PDF'

def process_file(input_path: Path, output_folder: Path, target_key: str, target_dims_str: str = None) -> dict:
    target_bytes = get_target_bytes(target_key)
    target_dims = parse_dimensions(target_dims_str) if target_dims_str else None
    
    ext = input_path.suffix.lower()
    
    res = {
        "original_name": input_path.name,
        "ok": False,
        "out_name": "",
        "out_size_bytes": 0,
        "method_used": ""
    }
    
    try:
        if ext in IMG_EXTS:
            img = Image.open(input_path)
            # Default to auto format selection
            out_data, fmt = compress_image_data(img, 'auto', target_bytes, target_dims)
            out_ext = '.' + fmt.lower()
            if out_ext == '.jpeg': out_ext = '.jpg'
            
            out_name = timestamp_name(input_path, out_ext)
            out_path = output_folder / out_name
            
            with open(out_path, 'wb') as f:
                f.write(out_data)
                
            res['ok'] = True
            res['out_name'] = out_name
            res['out_size_bytes'] = len(out_data)
            res['method_used'] = f"Image:{fmt}"
            if target_dims:
                res['method_used'] += f"+Resize({target_dims[0]}x{target_dims[1]})"
            
        elif ext in PDF_EXTS:
            # PDF resizing is complex, for now just compress
            out_data, fmt = compress_pdf(input_path, target_bytes)
            out_name = timestamp_name(input_path, '.pdf')
            out_path = output_folder / out_name
            
            with open(out_path, 'wb') as f:
                f.write(out_data)
                
            res['ok'] = True
            res['out_name'] = out_name
            res['out_size_bytes'] = len(out_data)
            res['method_used'] = "PDF:Raster+JPEG"
            
        else:
            res['method_used'] = "Skipped:Unsupported"
            
    except Exception as e:
        res['method_used'] = f"Error:{str(e)}"
        
    return res

def main():
    parser = argparse.ArgumentParser(description="Document Compressor CLI")
    parser.add_argument("input_path", help="Input file or directory")
    parser.add_argument("output_folder", help="Output directory")
    parser.add_argument("target_key", help="Target size key (e.g. 100kb)")
    
    args = parser.parse_args()
    
    input_p = Path(args.input_path)
    output_p = Path(args.output_folder)
    ensure_dir(output_p)
    
    results = []
    
    if input_p.is_file():
        results.append(process_file(input_p, output_p, args.target_key))
    elif input_p.is_dir():
        for child in input_p.iterdir():
            if child.is_file() and (child.suffix.lower() in IMG_EXTS or child.suffix.lower() in PDF_EXTS):
                results.append(process_file(child, output_p, args.target_key))
    else:
        print(f"Error: {input_p} not found")
        sys.exit(1)
        
    # Print table
    print(f"{'Original':<30} | {'Status':<6} | {'Out Size':<10} | {'Method'}")
    print("-" * 70)
    for r in results:
        size_str = readable_size(r['out_size_bytes']) if r['ok'] else "-"
        status = "OK" if r['ok'] else "FAIL"
        print(f"{r['original_name'][:30]:<30} | {status:<6} | {size_str:<10} | {r['method_used']}")
        
    # Exit code
    if any(not r['ok'] and "Error" in r['method_used'] for r in results):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
