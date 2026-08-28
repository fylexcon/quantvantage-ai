"""
Async Telegram webhook notifications for high-impact sentiment alerts.

Sends alerts via the Telegram Bot API when sentiment scores cross
significance thresholds.  Uses HTML parse_mode for robust formatting
(avoids MarkdownV2 special-character escaping issues).
"""

from __future__ import annotations

import html
import logging
import os

import httpx

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


def _build_message(ticker: str, sentiment: str, score: float, summary: str) -> str:
    """Build an HTML-formatted Telegram message body."""
    emoji = {"bullish": "🟢", "bearish": "🔴"}.get(sentiment.lower(), "⚪")
    direction = "+" if score >= 0 else ""

    # Truncate long summaries to keep Telegram messages readable
    safe_summary = html.escape(summary[:280]) if summary else "—"

    return (
        f"{emoji} <b>Sentiment Alert — ${html.escape(ticker.upper())}</b>\n\n"
        f"<b>Label:</b>  {html.escape(sentiment.capitalize())}\n"
        f"<b>Score:</b>  <code>{direction}{score:.2f}</code>\n\n"
        f"<b>Summary:</b>\n<i>{safe_summary}</i>"
    )


async def send_sentiment_alert(
    ticker: str,
    sentiment: str,
    score: float,
    summary: str,
) -> None:
    """Dispatch a Telegram alert if the sentiment event is significant.

    Significance criteria (any match triggers an alert):
      • ``abs(score) >= 0.7``
      • ``sentiment`` is ``"bullish"`` or ``"bearish"``

    The function is a silent no-op when:
      • The event does not meet the filter criteria.
      • ``TELEGRAM_BOT_TOKEN`` or ``TELEGRAM_CHAT_ID`` env vars are unset
        (keeps local development frictionless).
      • The Telegram API call fails (logged at *warning* level).
    """
    # ── Filter gate ──────────────────────────────────────────────────────
    is_strong_score = abs(score) >= 0.7
    is_directional = sentiment.lower() in ("bullish", "bearish")

    if not (is_strong_score or is_directional):
        return

    # ── Env-var guard (graceful no-op when unconfigured) ─────────────────
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        logger.debug(
            "Telegram alert skipped — TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set."
        )
        return

    # ── Build & send ─────────────────────────────────────────────────────
    url = f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": _build_message(ticker, sentiment, score, summary),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info(
                "Telegram alert sent for %s (score=%.2f, sentiment=%s)",
                ticker,
                score,
                sentiment,
            )
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Telegram API returned %s for %s alert: %s",
            exc.response.status_code,
            ticker,
            exc.response.text[:200],
        )
    except httpx.RequestError as exc:
        logger.warning(
            "Telegram alert network error for %s: %s",
            ticker,
            exc,
        )
