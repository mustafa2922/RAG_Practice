import unicodedata
import re

def remove_diacritics(text):
    # Normalize to NFD (decompose characters + diacritics)
    text = unicodedata.normalize("NFD", text)
    # Remove all combining marks (Arabic harakat)
    text = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)
    return unicodedata.normalize("NFC", text)

a = "دَارُ"
b = "دار"

# Compare after normalization
if remove_diacritics(a) == remove_diacritics(b):
    print("Equal ✅")
else:
    print("Not equal ❌")


print(remove_diacritics(a))