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
import html
import re
import unicodedata
import emoji
from langdetect import detect
import csv
from pathlib import Path


# Common internet slang dictionary.
# Additional entries can be added as needed.

def load_slang_map():
    csv_path = Path(__file__).parent
    slang_map = {}
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            slang_map[row["slang"].lower()] = row["expanded"]
    return slang_map

SLANG_MAP = load_slang_map()

# Regular expressions used during cleaning.
URL_PATTERN = r"http\S+|www\.\S+"
HTML_TAG_PATTERN = r"<[^>]+>"
MENTION_PATTERN = r"(?<!\w)@[\w.-]+"
ZERO_WIDTH_PATTERN = r"[\u200b-\u200f\u2060\ufeff]"


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as file:
        return json.load(file)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def remove_punctuation(text):
    text = re.sub(r"[^\w\s']", "", text)
    return text

def normalize_unicode(text):
    text = unicodedata.normalize("NFKC", text)
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def remove_noise(text):
    text = html.unescape(text)
    text = re.sub(URL_PATTERN, "", text)
    text = re.sub(HTML_TAG_PATTERN, " ", text)
    text = re.sub(ZERO_WIDTH_PATTERN, "", text)
    text = re.sub(MENTION_PATTERN, " ", text)
    text = re.sub(r"@[A-Za-z][A-Za-z0-9_.-]*\d+(?=[A-Za-z])", " ", text)
    text = re.sub(r"@\S+", " ", text)
    text = re.sub(r"#(\w+)", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def convert_emojis(text):
    text = emoji.demojize(text, delimiters=(" ", " "))
    text = re.sub(
        r"\b[A-Za-z]+(?:_[A-Za-z0-9-]+)+\b",
        lambda match: match.group(0).replace("_", " "),
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def normalize_slang(text):
    words = text.split()
    cleaned_words = []
    for word in words:
        cleaned_words.append(SLANG_MAP.get(word.lower(), word))
    return " ".join(cleaned_words)


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    text = re.sub(r"\s+([?.!,;:])", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


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
    if len(text.split()) < 2 and len(text.strip()) < 12:
        return True
    if re.fullmatch(r"[\W_]+", text):
        return True
    if text.lower() in ["nice", "lol", "ok", "cool", "first", "same", "thanks"]:
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
