"""Reject untranslated owned material without rewriting evidence or policies."""
import re
# Includes common, compatibility and supplementary unified ideographs.
HAN = re.compile('[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0003134f]')

def require_english_material(text, label):
    if HAN.search(text):
        raise ValueError('Untranslated CJK text in English material: '+label)
    return text
