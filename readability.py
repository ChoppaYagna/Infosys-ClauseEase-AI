# readability.py
# (CORRECTED: Added word-by-word complexity color-coding)

import re
import textstat
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# -------------------------------
# 1. Helper Functions
# -------------------------------

def calculate_sentiment(text):
    """
    Calculates sentiment using VADER.
    """
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    compound = sentiment['compound']
    
    if compound >= 0.05:
        label = "Positive"
    elif compound <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"
        
    return label, compound

def calculate_read_time(text):
    """
    Calculates estimated read time in minutes.
    """
    word_count = textstat.lexicon_count(text)
    # Average reading speed is ~200 WPM
    read_time_minutes = word_count / 200
    # Return at least 1 minute if there's any text, 0 if empty
    if word_count == 0:
        return 0
    return max(1, round(read_time_minutes))

# -------------------------------
# 2. Main Analytics Function (Called by app.py)
# -------------------------------

def analyze_readability(text):
    """
    Compute COMBINED metrics for the app.py dashboard.
    """
    # Check for empty or very short text
    if not text or len(text.split()) < 10:
        return {
            'flesch_kincaid': 0.0,
            'gunning_fog': 0.0,
            'flesch_ease': 0.0,
            'sentiment_label': 'Neutral',
            'sentiment_score': 0.0,
            'read_time_minutes': 0
        }
    
    try:
        # 1. Readability (using 'textstat' library)
        flesch_kincaid = textstat.flesch_kincaid_grade(text)
        gunning_fog = textstat.gunning_fog(text)
        flesch_ease = textstat.flesch_reading_ease(text)
        
        # 2. Sentiment (using VADER)
        sentiment_label, sentiment_score = calculate_sentiment(text)
        
        # 3. Read Time (using textstat)
        read_time_minutes = calculate_read_time(text)
        
        # 4. Return the combined dictionary structure
        return {
            'flesch_kincaid': flesch_kincaid,
            'gunning_fog': gunning_fog,
            'flesch_ease': flesch_ease,
            'sentiment_label': sentiment_label,
            'sentiment_score': sentiment_score,
            'read_time_minutes': read_time_minutes
        }
    except Exception as e:
        # Fallback on any error during calculation
        print(f"Error in analyze_readability: {e}") # Log error
        return {
            'flesch_kincaid': 0.0,
            'gunning_fog': 0.0,
            'flesch_ease': 0.0,
            'sentiment_label': 'Neutral',
            'sentiment_score': 0.0,
            'read_time_minutes': 0
        }

# -------------------------------
# 3. Highlight Function (Unchanged)
# -------------------------------

def highlight_legal_terms(text, glossary):
    """
    Highlights legal terms with tooltips using the .tooltip class from app.py.
    """
    def escape_html(text_to_escape):
        if not text_to_escape: return ""
        text_str = str(text_to_escape)
        return re.sub(r'[<>&]', lambda m: {'<':'&lt;', '>':'&gt;', '&':'&amp;'}[m.group()], text_str)

    escaped_text = escape_html(text)
    
    for term, definition in glossary.items():
        if isinstance(term, str) and isinstance(definition, str):
            try:
                pattern = re.compile(r'\b(' + re.escape(term) + r')\b', re.IGNORECASE)
                safe_definition = escape_html(definition)
                replacement = f'<span class="tooltip">\\1<span class="tooltiptext">{safe_definition}</span></span>'
                escaped_text = pattern.sub(replacement, escaped_text)
            except re.error as e:
                print(f"Regex error for term '{term}': {e}")
                pass 
    
    return escaped_text.replace('\n', '<br>')


# -------------------------------
# 4. *** NEW: Word-by-Word Complexity Analyzer ***
# -------------------------------

def color_code_complexity(text):
    """
    Analyzes text word-by-word for syllable complexity and returns an HTML string.
    """
    if not text:
        return ""

    # This regex finds all words (including hyphens) OR all whitespace (including newlines)
    tokens = re.finditer(r'([a-zA-Z0-9\-]+)|(\s+)', text)
    output_html = ""

    for token in tokens:
        word, space = token.groups()
        
        if word:
            # This is a word. Analyze it.
            try:
                syllables = textstat.syllable_count(word)
            except Exception:
                syllables = 1 # Default for weird tokens

            if syllables >= 3:
                css_class = 'word-complex'
            elif syllables == 2:
                css_class = 'word-medium'
            else:
                css_class = 'word-simple'
            
            output_html += f'<span class="{css_class}">{word}</span>'
        
        elif space:
            # This is whitespace. Preserve it.
            # Convert newlines to <br> for HTML rendering
            output_html += space.replace('\n', '<br>')

    return output_html