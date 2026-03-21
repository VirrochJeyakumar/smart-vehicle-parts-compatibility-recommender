# Aim of this section is 1) Text Normalisation

# Take the messy, unstructured text listing and convert it to a 
# more predictable, clean text version so every later step becomes
# easier and more reliable

# Done in steps, including: lowercase all text, standardise /, _ and |
# to be of same type in all listings, make multiple spaces into one and
# finally trim any whitespace

# example
# before normalisation: "Kawasaki ZX6R 07-12"
# after normalisation: "kawasaki zx6r 07-12"

# using regular expressions module
import re

def normalise_text(text: str) -> str:
    if not text:
        return ""
    
    # 1) convert to lowercase
    text = text.lower()

    # 2) standardise /, _ and -
    text = re.sub(r"[_/|]", " ", text)
    text = re.sub(r"[–—]", "-", text)

    # 3) remove multiple spaces (unnecessary whitespace)
    text = re.sub(r"\s+", " ", text).strip()

    return text
