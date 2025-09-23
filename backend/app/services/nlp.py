# backend/app/services/nlp.py
from transformers import pipeline

# Load Hugging Face sentiment-analysis pipeline
# You can pick a model, e.g. "distilbert-base-uncased-finetuned-sst-2-english"
sentiment_analyzer = pipeline("sentiment-analysis")

def analyze_mood(text: str) -> dict:
    """
    Uses Hugging Face transformers to analyze sentiment of the text.
    Returns the label (POSITIVE/NEGATIVE/NEUTRAL) and confidence score.
    """
    results = sentiment_analyzer(text[:512])  # truncate long inputs
    result = results[0]

    label = result["label"].lower()  # "POSITIVE" → "positive"
    score = float(result["score"])

    # Optionally normalize "neutral" if needed
    if label not in ["positive", "negative"]:
        label = "neutral"

    return {"mood": label, "score": score}
