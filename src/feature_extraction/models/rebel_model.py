"""
rebel_model.py

Relation extraction using REBEL.

Loads the model only when relation extraction is actually run.
Set RELATION_BACKEND=off to skip it for quick testing.
"""

import os
import re


MODEL_NAME = "Babelscape/rebel-large"

tokenizer = None
model = None
device = None


def load_rebel_model():
    global tokenizer, model, device

    if model is not None:
        return tokenizer, model, device

    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    return tokenizer, model, device


def clean_text_part(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def parse_rebel_output(decoded):
    relations = []

    for chunk in decoded.split("<triplet>"):
        if "<subj>" not in chunk or "<obj>" not in chunk:
            continue

        try:
            subject = clean_text_part(chunk.split("<subj>")[0])
            rest = chunk.split("<subj>")[1]
            obj = clean_text_part(rest.split("<obj>")[0])
            relation = clean_text_part(rest.split("<obj>")[1])
        except IndexError:
            continue

        if subject and relation and obj:
            relations.append(
                {
                    "subject": subject,
                    "relation": relation,
                    "object": obj,
                    "relation_text": f"{relation}({subject}, {obj})",
                    "matched_rule": "rebel_seq2seq",
                }
            )

    return relations


def analyze_relations(text):
    if not text or os.getenv("RELATION_BACKEND", "rebel").lower() == "off":
        return {
            "relation_count": 0,
            "relations": [],
        }

    import torch

    active_tokenizer, active_model, active_device = load_rebel_model()
    inputs = active_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    inputs = {key: value.to(active_device) for key, value in inputs.items()}

    with torch.no_grad():
        output = active_model.generate(**inputs, max_length=256)

    decoded = active_tokenizer.decode(output[0], skip_special_tokens=False)
    relations = parse_rebel_output(decoded)

    return {
        "relation_count": len(relations),
        "relations": relations,
    }
