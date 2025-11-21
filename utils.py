import os
import re

def is_google_configured():
    """Checks if the client_secrets.json file exists."""
    return os.path.exists('client_secrets.json')

LEGAL_KEYWORDS = ['agreement', 'contract', 'party', 'parties', 'whereas', 'heretofore', 'hereinafter', 'jurisdiction', 'liability', 'indemnify', 'indemnification', 'clause', 'article', 'section', 'subsection', 'governing law', 'termination', 'confidentiality', 'intellectual property', 'warranty', 'disclaimer', 'force majeure', 'arbitration', 'litigation', 'notwithstanding', 'pursuant', 'licensor', 'licensee', 'lessor', 'lessee']
LEGAL_KEYWORD_PATTERN = re.compile(r'\b(?:' + '|'.join(re.escape(k) for k in LEGAL_KEYWORDS) + r')\b', re.IGNORECASE)

def is_likely_legal(text, threshold=0.01):
    """Checks text for legal keyword density."""
    if not text or len(text.split()) < 50: return None
    matches = LEGAL_KEYWORD_PATTERN.findall(text)
    keyword_density = len(matches) / len(text.split())
    return keyword_density >= threshold


def get_word_count(text: str):
    """Counts words using textstat with a fallback."""
    # This function is lazy-loaded
    import textstat
    if not text or not isinstance(text, str):
        return 0
    try:
        return textstat.lexicon_count(text)
    except Exception:
        return len(text.split()) # Fallback