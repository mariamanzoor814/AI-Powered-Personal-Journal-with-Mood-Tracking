# backend/app/services/nlp.py
from __future__ import annotations
import time
import logging
from typing import Dict, Any, Optional, Tuple

import requests
import os
from urllib.parse import urljoin

from app.core.config import settings

logger = logging.getLogger(__name__)

HF_API_BASE = "https://api-inference.huggingface.co/models"

# classifier models
SENTIMENT_MODEL = getattr(
    settings,
    "HF_SENTIMENT_MODEL",
    "distilbert/distilbert-base-uncased-finetuned-sst-2-english",
)
EMOTION_MODEL = getattr(
    settings,
    "HF_EMOTION_MODEL",
    "j-hartmann/emotion-english-distilroberta-base",
)

HF_API_TOKEN = getattr(settings, "HF_API_TOKEN", None)
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}

# DeepL / translator config (read from settings/.env)
TRANSLATE_API_KEY = getattr(settings, "TRANSLATE_API_KEY", None)
# Default to the free API endpoint; change to "https://api.deepl.com/v2/translate" for paid account
TRANSLATE_API_URL = getattr(
    settings, "TRANSLATE_API_URL", "https://api-free.deepl.com/v2/translate"
)
TRANSLATE_TIMEOUT = getattr(settings, "TRANSLATE_TIMEOUT", 15)  # seconds

# safe defaults
DEFAULT_ANALYSIS = {
    "sentiment": "unknown",
    "emotion": "unknown",
    "sentiment_score": 0.0,
    "emotion_score": 0.0,
    "score": 0.0,
    "recommendation": "No analysis available right now.",
}


def _call_hf_model(
    model_name: str,
    text: str,
    top_k: Optional[int] = None,
    retries: int = 3,
    timeout: int = 120,
    backoff_factor: float = 1.2,
    parameters: Optional[dict] = None,
) -> Any:
    """
    Call Hugging Face Inference API with retries and model-loading handling.
    """
    if not HF_API_TOKEN:
        raise RuntimeError("HF_API_TOKEN is not set. Set it in your .env or settings.")

    url = f"{HF_API_BASE}/{model_name}"
    payload = {"inputs": text}
    if top_k is not None:
        payload["parameters"] = {"top_k": top_k}
    if parameters:
        payload["parameters"] = {**payload.get("parameters", {}), **parameters}

    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, headers=HEADERS, json=payload, timeout=timeout)
        except requests.RequestException as exc:
            logger.warning("HF request exception (attempt %d/%d): %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(backoff_factor * attempt)
                continue
            raise

        try:
            data = resp.json()
        except ValueError:
            resp.raise_for_status()

        if resp.status_code == 200:
            if isinstance(data, dict) and data.get("error"):
                err = data.get("error", "")
                if "loading" in err.lower() and attempt < retries:
                    time.sleep(backoff_factor * attempt)
                    continue
                raise RuntimeError(f"HuggingFace error: {err}")
            return data
        elif resp.status_code in (502, 503, 504):
            if attempt < retries:
                time.sleep(backoff_factor * attempt)
                continue
            resp.raise_for_status()
        else:
            resp.raise_for_status()

    raise RuntimeError("HF Inference: max retries exceeded")


def _extract_top(result: Any) -> Dict[str, Any]:
    if result is None:
        return {"label": "unknown", "score": 0.0}
    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, list) and first:
            return first[0] if isinstance(first[0], dict) else {"label": "unknown", "score": 0.0}
        if isinstance(first, dict):
            return first
    if isinstance(result, dict) and "label" in result:
        return result
    return {"label": "unknown", "score": 0.0}


# ---------------------------
# DeepL translator integration
# ---------------------------
def translate_text_to_english(text: str) -> Tuple[str, str]:
    """
    Translate `text` to English using DeepL API.
    Returns (translated_text, detected_language) on success.
    On failure returns (original_text, "unknown").
    """
    if not text:
        return "", "unknown"

    if not TRANSLATE_API_KEY:
        logger.warning("TRANSLATE_API_KEY not set — skipping translation.")
        return text, "unknown"

    logger.info(f"[DeepL] Sending text for translation: {text[:80]}...")

    url = TRANSLATE_API_URL
    payload = {
        "auth_key": TRANSLATE_API_KEY,
        "text": text,
        "target_lang": "EN",
    }
    try:
        resp = requests.post(url, data=payload, timeout=TRANSLATE_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        translations = data.get("translations", [])
        if translations and isinstance(translations, list):
            first = translations[0]
            translated = first.get("text", "") or ""
            detected = first.get("detected_source_language", "unknown")
            logger.info(f"[DeepL] Detected language={detected}, Translated text={translated[:80]}...")
            return translated, (detected or "unknown")

        logger.debug("DeepL returned unexpected shape: %s", data)
        return text, "unknown"

    except requests.RequestException as exc:
        logger.warning(f"[DeepL] Request failed: {exc}")
        return text, "unknown"
    except Exception as exc:
        logger.exception(f"[DeepL] Unexpected error: {exc}")
        return text, "unknown"



# -------------------------
# Core sentiment/emotion flow
# -------------------------
PROMPT_MAP = {
    "happy": "Celebrate your joy — share your light with others!",
    "sad": "This too shall pass. Brighter days are ahead.",
    "angry": "Breathe deeply. Choose calm over chaos.",
    "fear": "You are stronger than your worries. Face them step by step.",
    "surprise": "Embrace the unexpected — new paths bring growth.",
    "love": "Cherish the connections that warm your heart.",
    "joy": "Let gratitude amplify your happiness.",
    "trust": "Believe in your journey — you’re on the right path.",
    "anticipation": "Stay hopeful, good things are coming.",
    "disgust": "Release what doesn’t serve you, and move forward clean.",
    "shame": "Mistakes don’t define you. Growth does.",
    "guilt": "Forgive yourself — every day is a new chance.",
    "lonely": "You’re never truly alone — your story matters.",
    "confused": "Clarity comes with patience. Trust the process.",
    "overwhelmed": "Take one step at a time — you’ve got this.",
    "grateful": "Keep noticing the little blessings around you.",
    "inspired": "Let this spark move you closer to your dreams.",
    "proud": "Celebrate your wins, no matter how small.",
    "calm": "Stay grounded — peace is your strength.",
    "hopeful": "Hold on — tomorrow carries promise.",
    "hurt": "Healing takes time, but you are resilient.",
    "anxious": "Breathe. You’re safe in this moment.",
    "stressed": "Pause, recharge, and return stronger.",
    "content": "Enjoy the stillness — happiness lives here.",
    "bored": "Explore something new — curiosity fuels growth.",
    "determined": "Keep pushing — your persistence will pay off.",
    "optimistic": "Your mindset shapes your future. Stay bright.",
    "negative": "Hardships don’t last — your strength does.",
    "positive": "Keep shining — you inspire others too.",
    "neutral": "Every day holds potential. Make it meaningful.",
}


def get_recommendation(sentiment: str, emotion: str, score: float) -> str:
    emotion_key = emotion.lower().strip()
    if emotion_key in PROMPT_MAP:
        return PROMPT_MAP[emotion_key]

    sentiment_key = sentiment.lower().strip()
    if sentiment_key in PROMPT_MAP:
        return PROMPT_MAP[sentiment_key]

    return "Keep moving forward — you are doing better than you think."


def analyze_mood(text: str) -> Dict[str, Any]:
    """
    Translate incoming text to English (DeepL) then run HF sentiment + emotion.
    Returns analysis dict including translation metadata.
    """
    if not text:
        return {**DEFAULT_ANALYSIS}

    # --- Translate first (best-effort) ---
    translated_text, detected_lang = translate_text_to_english(text)

    # Use translated text if available; otherwise fall back to original text
    text_input = (translated_text or text)[:1500]
    logger.info(f"[Mood Analysis] Using text for HF analysis: {text_input[:80]}...")


    if not HF_API_TOKEN:
        logger.warning("HF_API_TOKEN not set — returning default analysis.")
        base = {**DEFAULT_ANALYSIS}
        base.update({"translated_text": translated_text, "detected_language": detected_lang})
        return base

    try:
        sent_raw = _call_hf_model(SENTIMENT_MODEL, text_input)
    except Exception as e:
        logger.exception("Sentiment model call failed: %s", e)
        return {
            **DEFAULT_ANALYSIS,
            "translated_text": translated_text,
            "detected_language": detected_lang,
        }

    try:
        emo_raw = _call_hf_model(EMOTION_MODEL, text_input, top_k=1)
    except Exception as e:
        logger.warning("Emotion model call failed: %s", e)
        emo_raw = None

    s = _extract_top(sent_raw)
    e = _extract_top(emo_raw) if emo_raw is not None else {"label": "unknown", "score": 0.0}

    sent_label = (s.get("label") or "").strip().lower()
    if "pos" in sent_label or "positive" in sent_label:
        sentiment = "positive"
    elif "neg" in sent_label or "negative" in sent_label:
        sentiment = "negative"
    elif sent_label in ("neutral", "none", ""):
        sentiment = "neutral"
    else:
        sentiment = sent_label or "unknown"

    emotion = (e.get("label") or "unknown").strip().lower()

    try:
        sentiment_score = float(s.get("score", 0.0))
    except Exception:
        sentiment_score = 0.0
    try:
        emotion_score = float(e.get("score", 0.0))
    except Exception:
        emotion_score = 0.0

    if emotion == "unknown":
        combined_score = sentiment_score
    else:
        combined_score = (sentiment_score + emotion_score) / 2.0

    recommendation = get_recommendation(sentiment, emotion, combined_score)

    return {
        "sentiment": sentiment,
        "emotion": emotion,
        "sentiment_score": round(sentiment_score, 4),
        "emotion_score": round(emotion_score, 4),
        "score": round(combined_score, 4),
        "recommendation": recommendation,
        "translated_text": translated_text,
        "detected_language": detected_lang,
    }
