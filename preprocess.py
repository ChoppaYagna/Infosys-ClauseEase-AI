import os
import fitz  # PyMuPDF for PDFs
import docx2txt
import pytesseract
from PIL import Image
import re
import tempfile

# CORRECT spellchecker import
try:
    from spellchecker import SpellChecker
    SPELL_CHECKER_AVAILABLE = True
    spell = SpellChecker()
except ImportError:
    SPELL_CHECKER_AVAILABLE = False
    print("SpellChecker not available. Continuing without spell checking.")

# -------------------------------
#  CLEANING + NORMALIZATION
# -------------------------------

def clean_text(text):
    if not text:
        return ""
    
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    text = re.sub(r'\n{2,}', '\n\n', text)
    text = re.sub(r'[^a-zA-Z0-9\s\n\-.,()₹$#/%]+', '', text) 
    return text.strip()

# -------------------------------
#  SPELL CHECKING (Optional)
# -------------------------------

def correct_spelling(text, glossary_words=None):
    """Optional spell checking - only works if pyspellchecker is installed."""
    if not SPELL_CHECKER_AVAILABLE or not text:
        return text
        
    glossary_words = set(w.lower() for w in glossary_words) if glossary_words else set()

    corrected_words = []
    for word in text.split():
        lw = word.lower()

        if (lw in glossary_words or not word.isalpha() or len(word) <= 2):
            corrected_words.append(word)
            continue

        try:
            corrected = spell.correction(word)
            corrected_words.append(corrected if corrected else word)
        except:
            corrected_words.append(word)

    return ' '.join(corrected_words)

# -------------------------------
#  TEXT EXTRACTION FUNCTIONS
# -------------------------------

def extract_text_from_pdf(file_path, glossary_words=None):
    text = ""
    try:
        with fitz.open(file_path) as pdf:
            for page in pdf:
                page_rect = page.rect
                page_height = page_rect.height
                header_margin = page_height * 0.10
                footer_margin = page_height * 0.90
                
                blocks = page.get_text("blocks")
                main_content_blocks = []
                for b in blocks:
                    x0, y0, x1, y1, block_text, _, _ = b
                    if y0 > header_margin and y1 < footer_margin:
                        main_content_blocks.append(block_text)
                
                text += "\n".join(main_content_blocks)
        
        cleaned = clean_text(text)
        
        # Optional: Enable spell checking for PDFs (often have OCR errors)
        # if SPELL_CHECKER_AVAILABLE:
        #     return correct_spelling(cleaned, glossary_words)
        
        return cleaned
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF: {e}")

# ... (rest of the functions remain the same as the first version)

def extract_text_from_docx(file_path, glossary_words=None):
    try:
        text = docx2txt.process(file_path)
        cleaned = clean_text(text)
        return cleaned
    except Exception as e:
        raise ValueError(f"Error extracting text from DOCX: {e}")

def extract_text_from_image(file_path_or_obj, glossary_words=None):
    try:
        image = Image.open(file_path_or_obj)
        text = pytesseract.image_to_string(image)
        cleaned = clean_text(text)
        return cleaned
    except Exception as e:
        raise ValueError(f"Error extracting text from image: {e}")

def extract_text_from_txt(file_path_or_obj, glossary_words=None):
    try:
        if hasattr(file_path_or_obj, "read"):
            text = file_path_or_obj.read().decode('utf-8', errors='ignore')
        else:
            with open(file_path_or_obj, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        cleaned = clean_text(text)
        return cleaned
    except Exception as e:
        raise ValueError(f"Error extracting text from TXT: {e}")

def extract_text_from_upload(uploaded_file, glossary_words=None, use_ocr=False):
    if uploaded_file is None:
        raise ValueError("No file provided")
        
    ext = os.path.splitext(uploaded_file.name)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    try:
        if ext == '.pdf':
            return extract_text_from_pdf(tmp_path, glossary_words)
        elif ext == '.docx':
            return extract_text_from_docx(tmp_path, glossary_words)
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']:
            return extract_text_from_image(tmp_path, glossary_words)
        elif ext == '.txt':
            return extract_text_from_txt(tmp_path, glossary_words)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    except Exception as e:
        raise ValueError(f"Error processing file '{uploaded_file.name}': {e}")
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass