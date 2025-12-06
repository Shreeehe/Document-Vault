import os
import re
from pathlib import Path
from datetime import datetime
from typing import Union, Tuple, Optional

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists and return Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def readable_size(size_in_bytes: int) -> str:
    """Convert bytes to readable string (e.g., 12.3 KB)."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB"

def parse_size_str(size_str: str) -> int:
    """Parse size string like '100kb', '1mb' to bytes."""
    s = size_str.strip().lower()
    if s.endswith('kb'):
        return int(float(s[:-2]) * 1024)
    elif s.endswith('mb'):
        return int(float(s[:-2]) * 1024 * 1024)
    elif s.endswith('b'):
        return int(s[:-1])
    try:
        return int(s)
    except ValueError:
        # Default fallback if parsing fails, though shouldn't happen with controlled inputs
        return 100 * 1024

def parse_dimensions(dim_str: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse dimension string like '3.5x4.5cm', '51x51mm', '200x200px'.
    Returns (width_px, height_px) assuming 300 DPI for physical units.
    """
    if not dim_str:
        return None, None
        
    s = dim_str.lower().replace(" ", "")
    
    # Extract numbers and unit
    # Regex for "WxHunit"
    m = re.match(r"([\d\.]+)[x×]([\d\.]+)([a-z]+)", s)
    if not m:
        return None, None
        
    w, h, unit = float(m.group(1)), float(m.group(2)), m.group(3)
    
    dpi = 300
    
    if unit == 'cm':
        # 1 inch = 2.54 cm
        w_px = int(w / 2.54 * dpi)
        h_px = int(h / 2.54 * dpi)
    elif unit == 'mm':
        w_px = int(w / 25.4 * dpi)
        h_px = int(h / 25.4 * dpi)
    elif unit == 'inch' or unit == 'in':
        w_px = int(w * dpi)
        h_px = int(h * dpi)
    elif unit == 'px':
        w_px = int(w)
        h_px = int(h)
    else:
        return None, None
        
    return w_px, h_px

def timestamp_name(original_path: Union[str, Path], ext: str = None) -> str:
    """Generate a timestamped filename based on original."""
    p = Path(original_path)
    stem = p.stem
    extension = ext if ext else p.suffix
    if not extension.startswith('.'):
        extension = '.' + extension
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stem}_compressed_{ts}{extension}"

def safe_write_bytes(path: Union[str, Path], data: bytes) -> None:
    """Write bytes to file safely."""
    p = Path(path)
    ensure_dir(p.parent)
    with open(p, 'wb') as f:
        f.write(data)
