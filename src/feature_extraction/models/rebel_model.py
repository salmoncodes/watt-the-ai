"""
rebel_model.py
Relation extraction using REBEL.
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch


MODEL_NAME = "Babelscape/rebel-large"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()

def analyze_relations(text):
    if not text:
        return {
          "relation_count": 0,
          "relations": []
        }
      
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        output = model.generate(**inputs, max_length=256)
    decoded = tokenizer.decode(output[0], skip_special_tokens=False)
    relations = []
    for chunk in decoded.split("<triplet>"):
        if "<subj>" not in chunk or "<obj>" not in chunk:
            continue
        try:
            subject = chunk.split("<subj>")[0].strip()
            rest = chunk.split("<subj>")[1]
            obj = rest.split("<obj>")[0].strip()
            relation = rest.split("<obj>")[1].strip()
            relations.append(
              {
                    "subject": subject,
                    "relation": relation,
                    "object": obj
                }
            )
        except:
            continue
          
    return {
        "relation_count": len(relations),
        "relations": relations
    }
