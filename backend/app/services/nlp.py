# backend/app/services/nlp.py
from transformers import pipeline

# Load Hugging Face pipelines
# Using a good, general-purpose emotion model, e.g., 'j-hartmann/emotion-english-distilroberta-base'
sentiment_analyzer = pipeline("sentiment-analysis", model="finiteautomata/bert-base-uncased-sst2")
emotion_analyzer = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=1)

def analyze_mood(text: str) -> dict:
    """
    Uses Hugging Face transformers to analyze sentiment and emotion of the text.
    """
    # Truncate long inputs for the models (max is typically 512 tokens)
    text_input = text[:512]

    # --- Sentiment Analysis ---
    sentiment_results = sentiment_analyzer(text_input)[0]
    sentiment_label = sentiment_results["label"].lower()
    sentiment_score = float(sentiment_results["score"])
    
    # Normalize sentiment label to 'positive', 'negative', or 'neutral'
    if sentiment_label not in ["positive", "negative"]:
        sentiment_label = "neutral" 
    
    # --- Emotion Analysis (Top 1) ---
    emotion_results = emotion_analyzer(text_input)[0][0] # Get the single result dict
    emotion_label = emotion_results["label"].lower()
    emotion_score = float(emotion_results["score"])

    return {
        "sentiment": sentiment_label, 
        "emotion": emotion_label, 
        # Using a general 'score' as the average, or you can pick one
        "score": (sentiment_score + emotion_score) / 2
    }