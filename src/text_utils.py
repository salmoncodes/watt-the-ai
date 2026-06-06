"""
text_utils.py

Shared utility functions used by all preprocessing pipelines.

This module contains reusable functions for:
- Loading and saving JSON files
- Text normalization
- Noise removal
- Emoji conversion
- Slang normalization
- Language detection
- Spam detection
- Deduplication

All preprocessing pipelines import these utilities.
"""

import json
import re
import unicodedata
import emoji
from langdetect import detect


# Common internet slang dictionary.
# Additional entries can be added as needed.
SLANG_MAP = {
    "idk": "i do not know",
    "ngl": "not gonna lie",
    "imo": "in my opinion",
    "lmao": "laughing",
    "bruh": "disbelief",
    "wtf": "what the hell",
    "omg": "oh my god"
}


# Regular expressions used during cleaning.
URL_PATTERN = r"http\S+|www\.\S+"
HTML_PATTERN = r"&\w+;"


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def normalize_unicode(text):
    return unicodedata.normalize("NFKC", text)


def remove_noise(text):
    text = re.sub(URL_PATTERN, "", text)
    text = re.sub(HTML_PATTERN, "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def convert_emojis(text):
    return emoji.demojize(text, delimiters=(" ", " "))


def normalize_slang(text):
    words = text.split()
    cleaned_words = []
    for word in words:
        cleaned_words.append(SLANG_MAP.get(word.lower(), word))
    return " ".join(cleaned_words)


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    return text


def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"


def filter_language(text, target_language="en"):
    language = detect_language(text)
    if language != target_language:
        return None
    return text


def is_spam(text):
    if len(text.strip()) < 3:
        return True
    if re.fullmatch(r"[\W_]+", text):
        return True
    if text.lower() in ["nice", "lol", "ok", "cool"]:
        return True
    return False


def deduplicate(records, key_fields):
    seen = set()
    unique = []
    for record in records:
        key = tuple(record.get(field) for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique
