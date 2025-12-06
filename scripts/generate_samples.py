from PIL import Image, ImageDraw
import fitz
import os

def gen_samples():
    os.makedirs("examples/sample_inputs", exist_ok=True)
    
    # JPG
    img = Image.new('RGB', (100, 100), color = 'red')
    d = ImageDraw.Draw(img)
    d.text((10,10), "Sample JPG", fill=(255,255,255))
    img.save("examples/sample_inputs/sample.jpg")
    
    # PNG
    img = Image.new('RGB', (100, 100), color = 'blue')
    d = ImageDraw.Draw(img)
    d.text((10,10), "Sample PNG", fill=(255,255,255))
    img.save("examples/sample_inputs/sample.png")
    
    # PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Sample PDF Document")
    doc.save("examples/sample_inputs/sample.pdf")
    
if __name__ == "__main__":
    gen_samples()
