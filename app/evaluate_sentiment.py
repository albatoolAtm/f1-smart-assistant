# app/evaluate_sentiment.py

import json
import os
import re
from typing import List

from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

from app.agents.nlp_agent import analyze_sentiment


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "f1_labeled_comments.json")
REPORT_FILE = os.path.join(BASE_DIR, "data", "sentiment_eval_report.txt")


def detect_lang(text: str) -> str:
    """بسيطة: لو فيه حروف عربية يرجع 'ar' غير كذا 'en'."""
    if re.search(r"[\u0600-\u06FF]", text or ""):
        return "ar"
    return "en"


def load_dataset(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts: List[str] = []
    labels: List[str] = []

    for item in data:
        t = item.get("text", "").strip()
        y = item.get("label", "").strip().lower()
        if not t or y not in {"positive", "negative", "neutral"}:
            continue
        texts.append(t)
        labels.append(y)

    return texts, labels


def main():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Dataset not found at {DATA_FILE}")

    print(f"Loading dataset from {DATA_FILE} ...")
    texts, y_true = load_dataset(DATA_FILE)
    print(f"Loaded {len(texts)} labeled examples.")

    y_pred: List[str] = []

    for i, text in enumerate(texts, start=1):
        lang = detect_lang(text)
        result = analyze_sentiment(text, language=lang)
        pred_label = result.get("label", "neutral")
        y_pred.append(pred_label)

        print(f"[{i}/{len(texts)}] true={y_true[i-1]}, pred={pred_label}")

    # ====== 1) Accuracy & F1 ======
    acc = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average="macro")
    f1_weighted = f1_score(y_true, y_pred, average="weighted")

    # ====== 2) Detailed report ======
    report = classification_report(
        y_true,
        y_pred,
        target_names=["negative", "neutral", "positive"],
        labels=["negative", "neutral", "positive"]
    )

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=["negative", "neutral", "positive"]
    )

    # ====== 3) Print to console ======
    print("\n===== SENTIMENT EVALUATION =====")
    print(f"Accuracy      : {acc:.3f}")
    print(f"F1 (macro)    : {f1_macro:.3f}")
    print(f"F1 (weighted) : {f1_weighted:.3f}")
    print("\nClassification report:\n")
    print(report)
    print("Confusion matrix [rows=true, cols=pred]:")
    print("      neg  neu  pos")
    for row_label, row in zip(["neg", "neu", "pos"], cm):
        print(f"{row_label:>4}  {row[0]:>3}  {row[1]:>3}  {row[2]:>3}")

    # ====== 4) Save to file ======
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("===== SENTIMENT EVALUATION =====\n")
        f.write(f"Accuracy      : {acc:.3f}\n")
        f.write(f"F1 (macro)    : {f1_macro:.3f}\n")
        f.write(f"F1 (weighted) : {f1_weighted:.3f}\n\n")
        f.write("Classification report:\n")
        f.write(report)
        f.write("\n\nConfusion matrix [rows=true, cols=pred]:\n")
        f.write("      neg  neu  pos\n")
        for row_label, row in zip(["neg", "neu", "pos"], cm):
            f.write(f"{row_label:>4}  {row[0]:>3}  {row[1]:>3}  {row[2]:>3}\n")

    print(f"\nSaved evaluation report to {REPORT_FILE}")


if __name__ == "__main__":
    main()
