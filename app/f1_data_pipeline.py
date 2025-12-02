# app/f1_data_pipeline.py

import json
import re
import string
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer

from gensim.models import Word2Vec

# ========= 0) Setup NLTK =========
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)

STOPWORDS = set(stopwords.words("english"))
STEMMER = PorterStemmer()
LEMMATIZER = WordNetLemmatizer()


def clean_text(text: str) -> str:
    """Lowercase + remove punctuation."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text


def preprocess_text(text: str):
    """Tokenize → Remove Stopwords → Stem → Lemmatize"""
    cleaned = clean_text(text)
    tokens = nltk.word_tokenize(cleaned)
    tokens = [t for t in tokens if t not in STOPWORDS]

    stems = [STEMMER.stem(t) for t in tokens]
    lemmas = [LEMMATIZER.lemmatize(t) for t in tokens]

    return {
        "cleaned": cleaned,
        "tokens": tokens,
        "stems": stems,
        "lemmas": lemmas,
    }


# ========= 1) Load Datasets =========
BASE = Path(__file__).parent

calendar_path = BASE / "race_calendar.json"
passages_path = BASE / "models" / "passages.json"
telemetry_path = BASE / "models" / "telemetry_embeddings.json"

race_calendar = json.loads(calendar_path.read_text())
passages = json.loads(passages_path.read_text())
telemetry = json.loads(telemetry_path.read_text())

print("Loaded datasets:")
print(f"- Calendar entries: {len(race_calendar.get('races', []))}")
print(f"- Passages entries: {len(passages)}")
print(f"- Telemetry drivers: {len(telemetry)}")


# ========= 2) Process Text Datasets =========

processed_passages = []

for item in passages:
    text = item.get("text", "")
    processed = preprocess_text(text)

    processed_passages.append({
        "original": text,
        "cleaned": processed["cleaned"],
        "tokens": processed["tokens"],
        "stems": processed["stems"],
        "lemmas": processed["lemmas"],
        "source": item.get("source"),
    })

# ========= 3) Train Word2Vec Model (on passages dataset) =========

sentences = [p["tokens"] for p in processed_passages]
word2vec_model = Word2Vec(
    sentences,
    vector_size=50,
    window=5,
    min_count=1,
    workers=4
)

word2vec_model.save("f1_word2vec.model")

print("Word2Vec trained and saved → f1_word2vec.model")

# ========= 4) Save Processed Output =========

output_file = BASE / "processed_passages.json"
output_file.write_text(json.dumps(processed_passages, indent=4))

print(f"Processed passages saved → {output_file}")

