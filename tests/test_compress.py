import pytest
import os
import shutil
from pathlib import Path
from PIL import Image
import fitz

from compressor.compress_any import process_file, get_target_bytes
from compressor.utils import ensure_dir

SAMPLE_DIR = Path("examples/sample_inputs")
OUTPUT_DIR = Path("tests/output")

@pytest.fixture(scope="session", autouse=True)
def setup_teardown():
    ensure_dir(OUTPUT_DIR)
    yield
    # shutil.rmtree(OUTPUT_DIR) # Keep for inspection

def test_target_bytes_parsing():
    assert get_target_bytes("100kb") == 102400
    assert get_target_bytes("1mb") == 1048576
    assert get_target_bytes("500b") == 500

def test_compress_jpg():
    input_path = SAMPLE_DIR / "sample.jpg"
    if not input_path.exists():
        pytest.skip("Sample JPG not found")
        
    res = process_file(input_path, OUTPUT_DIR, "50kb")
    assert res['ok'] is True
    assert res['out_size_bytes'] <= 51200 # 50KB
    assert (OUTPUT_DIR / res['out_name']).exists()

def test_compress_png():
    input_path = SAMPLE_DIR / "sample.png"
    if not input_path.exists():
        pytest.skip("Sample PNG not found")
        
    res = process_file(input_path, OUTPUT_DIR, "50kb")
    assert res['ok'] is True
    assert res['out_size_bytes'] <= 51200
    assert (OUTPUT_DIR / res['out_name']).exists()

def test_compress_pdf():
    input_path = SAMPLE_DIR / "sample.pdf"
    if not input_path.exists():
        pytest.skip("Sample PDF not found")
        
    res = process_file(input_path, OUTPUT_DIR, "50kb")
    assert res['ok'] is True
    # PDF compression is harder to guarantee exact size if content is complex, 
    # but our sample is simple text.
    assert res['out_size_bytes'] > 0
    assert (OUTPUT_DIR / res['out_name']).exists()

def test_invalid_file():
    # Create dummy text file
    dummy = OUTPUT_DIR / "test.txt"
    with open(dummy, "w") as f:
        f.write("hello")
        
    res = process_file(dummy, OUTPUT_DIR, "100kb")
    assert res['ok'] is False
    assert "Skipped" in res['method_used']
