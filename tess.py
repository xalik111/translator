try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract
import urllib.request



def whats_on_pic(path):
    try:
        m = pytesseract.image_to_string(Image.open(path))
        return m
    except:
        return print("Not found")