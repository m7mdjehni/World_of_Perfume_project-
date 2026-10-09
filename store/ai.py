"""Local AI-based perfume description generator.

Generates descriptions using a small local language model (distilgpt2)
via the `transformers` library — this is real AI text generation
(a neural network doing next-token prediction), not a templated string.

No external API and no API key are involved. The model's weights are
downloaded once from Hugging Face the first time the app runs (this one
step needs internet, the same as any `pip install`), then cached on disk
under ~/.cache/huggingface. Every call after that runs the model
completely locally/offline — no network request is made per description.

If the model can't be loaded (e.g. `transformers`/`torch` aren't
installed, or the weights haven't been downloaded yet and there's no
internet), generation falls back to a simple templated description so
the feature never breaks the rest of the app.
"""

import logging
import re
import threading

logger = logging.getLogger(__name__)

_generator = None
_load_lock = threading.Lock()
_load_failed = False


def _get_generator():
    """Lazily load the text-generation pipeline once per process, and
    reuse it for every later call (loading the model is slow; running it
    on an already-loaded model is fast)."""
    global _generator, _load_failed

    if _generator is not None:
        return _generator
    if _load_failed:
        return None

    with _load_lock:
        if _generator is None and not _load_failed:
            try:
                from transformers import pipeline
                _generator = pipeline("text-generation", model="distilgpt2")
            except Exception as exc:  # model/deps missing, no internet yet, etc.
                logger.warning("Could not load local AI model, using fallback: %s", exc)
                _load_failed = True
    return _generator


def generate_description(name: str, notes: str = "") -> str:
    """Return an AI-generated perfume description.

    Args:
        name: The perfume's name, e.g. "Midnight Oud".
        notes: Optional freeform scent notes, e.g. "amber, oud, vanilla".
    """
    name = (name or "").strip()
    notes = (notes or "").strip()

    if not name:
        return ""

    generator = _get_generator()
    if generator is None:
        return _fallback_description(name, notes)

    if notes:
        prompt = f"{name} is a luxury perfume with notes of {notes}. In one elegant sentence, it is best described as:"
    else:
        prompt = f"{name} is a luxury perfume. In one elegant sentence, it is best described as:"

    try:
        output = generator(
            prompt,
            max_new_tokens=40,
            num_return_sequences=1,
            do_sample=True,
            temperature=0.8,
            top_p=0.9,
            pad_token_id=generator.tokenizer.eos_token_id,
        )
        generated_text = output[0]["generated_text"][len(prompt):]
        description = _clean_generated_text(generated_text, name)
        return description or _fallback_description(name, notes)
    except Exception as exc:
        logger.warning("AI generation failed, using fallback: %s", exc)
        return _fallback_description(name, notes)


def _clean_generated_text(text: str, name: str) -> str:
    """Trim the model's raw continuation down to one or two clean sentences."""
    text = text.replace("\n", " ").strip()
    sentences = re.split(r'(?<=[.!?]) +', text)
    result = " ".join(s for s in sentences[:2] if s).strip()
    if not result:
        return ""
    if name not in result:
        result = f"{name} — {result}"
    return result


def _fallback_description(name: str, notes: str) -> str:
    if notes:
        return (
            f"{name} — a captivating fragrance featuring {notes}, "
            "crafted for those who appreciate timeless elegance."
        )
    return (
        f"{name} — a captivating fragrance crafted for those who "
        "appreciate timeless elegance."
    )
