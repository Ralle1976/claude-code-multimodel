"""
Komprimierungs-Engine: LLMLingua wenn verfuegbar, sonst regelbasierter Fallback.
"""

import os
import sys

from .storage import save_compression_stat

# LLMLingua Konfiguration
DEFAULT_COMPRESSION_RATE = 0.5  # 50% der Tokens behalten
DEFAULT_TARGET_TOKENS = 2000   # Ziel-Token-Anzahl


def llmlingua_disabled() -> bool:
    """Offline-Modus: verhindert Modell-Downloads in Tests und Air-Gapped-Setups."""
    return os.environ.get("CLAUDE_DISABLE_LLMLINGUA", "").lower() in {"1", "true", "yes"}


def load_llmlingua():
    """Laedt den LLMLingua-Kompressor (lazy, CPU-only)."""
    if llmlingua_disabled():
        return None

    try:
        from llmlingua import PromptCompressor
        return PromptCompressor(
            model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
            use_llmlingua2=True,
            device_map="cpu"  # CPU fuer WSL-Kompatibilitaet
        )
    except ImportError:
        return None
    except Exception as e:
        print(f"LLMLingua Ladefehler: {e}", file=sys.stderr)
        return None


def simple_compress(text: str, target_ratio: float = 0.5) -> str:
    """
    Regelbasierte Komprimierung ohne ML-Modell.

    Entfernt Fuellwoerter und behaelt bei Overlength Anfang und Ende.
    """
    import re

    text = re.sub(r'\s+', ' ', text).strip()

    filler_patterns = [
        r'\b(also|eigentlich|sozusagen|quasi|praktisch|grundsaetzlich|prinzipiell)\b',
        r'\b(basically|actually|literally|essentially|fundamentally)\b',
        r'\b(ich denke|ich glaube|ich meine|meiner Meinung nach)\b',
        r'\b(I think|I believe|I mean|in my opinion)\b',
    ]
    for pattern in filler_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    text = re.sub(r'\s+', ' ', text).strip()

    words = text.split()
    target_words = int(len(words) * target_ratio)
    if len(words) > target_words and target_words > 50:
        keep_start = target_words * 2 // 3
        keep_end = target_words - keep_start
        text = ' '.join(words[:keep_start]) + ' [...] ' + ' '.join(words[-keep_end:])

    return text


def compress_text(text: str, target_ratio: float = DEFAULT_COMPRESSION_RATE,
                  use_llmlingua: bool = True) -> dict:
    """
    Komprimiert Text mit LLMLingua oder dem regelbasierten Fallback.

    Args:
        text: Zu komprimierender Text
        target_ratio: Anteil der zu behaltenden Tokens (0.0-1.0)
        use_llmlingua: Wenn False, wird nur die einfache Komprimierung genutzt

    Returns:
        dict mit compressed_text, original_tokens, compressed_tokens, ratio
    """
    if not text or len(text.strip()) < 100:
        token_count = len(text.split()) if text else 0
        return {
            "success": True,
            "compressed_text": text,
            "original_tokens": token_count,
            "compressed_tokens": token_count,
            "compression_ratio": 1.0,
            "skipped": True,
            "reason": "Text zu kurz fuer Komprimierung"
        }

    if not 0 < target_ratio <= 1:
        return {
            "success": False,
            "error": "invalid_ratio",
            "message": f"ratio muss zwischen 0 (exklusiv) und 1 liegen, war: {target_ratio}"
        }

    compressor = load_llmlingua() if use_llmlingua else None

    if not compressor:
        original_tokens = len(text.split())
        compressed = simple_compress(text, target_ratio)
        compressed_tokens = len(compressed.split())

        save_compression_stat(original_tokens, compressed_tokens)

        return {
            "success": True,
            "compressed_text": compressed,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "compression_ratio": round(compressed_tokens / original_tokens, 3) if original_tokens > 0 else 1.0,
            "tokens_saved": original_tokens - compressed_tokens,
            "method": "simple" if use_llmlingua else "simple_only",
            "note": "Einfache Komprimierung (LLMLingua nicht verfuegbar)" if use_llmlingua else "Einfache Komprimierung"
        }

    try:
        result = compressor.compress_prompt(
            text,
            rate=target_ratio,
            force_tokens=['\n', '.', '!', '?', ','],  # Behalte wichtige Zeichen
            drop_consecutive=True
        )

        compressed = result["compressed_prompt"]
        original_tokens = result.get("origin_tokens", len(text.split()))
        compressed_tokens = result.get("compressed_tokens", len(compressed.split()))

        save_compression_stat(original_tokens, compressed_tokens)

        return {
            "success": True,
            "compressed_text": compressed,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "compression_ratio": round(compressed_tokens / original_tokens, 3) if original_tokens > 0 else 1.0,
            "tokens_saved": original_tokens - compressed_tokens
        }

    except Exception as e:
        return {
            "success": False,
            "error": "compression_failed",
            "message": f"Komprimierung fehlgeschlagen: {str(e)}"
        }
