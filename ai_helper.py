"""Uzbek AI Assistant powered by Gemini API when configured, with local smart fallback."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def _format_sum(amount: int) -> str:
    if amount == 0:
        return "Bepul"
    return f"{amount:,}".replace(",", " ") + " so'm"


def _build_context(state: dict[str, Any]) -> str:
    profile = state.get("profile", {})
    services = state.get("services", [])
    lines = [
        f"Biznes nomi: {profile.get('name', '')}",
        f"Yo'nalish: {profile.get('niche_label', '')}",
        f"Ish vaqti: {profile.get('hours', '')}",
        f"Manzil: {profile.get('address', '')}",
        f"Telefon: {profile.get('phone', '')}",
        "Xizmatlar va narxlar:",
    ]
    for s in services:
        lines.append(
            f"- {s['name']}: {_format_sum(s['price_uzs'])} ({s['duration_min']} daqiqa). {s['description']}"
        )
    return "\n".join(lines)


def _call_gemini(user_message: str, context: str, api_key: str) -> str | None:
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )
    prompt = (
        "Sen mahalliy biznesning samimiy va qisqa javob beradigan o'zbek tilidagi AI maslahatchisisan. "
        "Faqat quyidagi biznes ma'lumotlariga tayanib javob ber, mijozni buyurtma berishga yo'naltir.\n\n"
        f"{context}\n\nMijoz savoli: {user_message}"
    )
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"].strip()
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError):
        return None
    return None


def _local_fallback_reply(user_message: str, state: dict[str, Any]) -> str:
    msg = user_message.lower()
    profile = state.get("profile", {})
    services = state.get("services", [])

    # Check if user mentions a specific service keyword
    matched = [
        s
        for s in services
        if any(word in s["name"].lower() or word in s["description"].lower() for word in msg.split() if len(word) > 2)
    ]

    if any(k in msg for k in ("narx", "qancha", "necha", "sum", "so'm", "xizmat", "menyu", "kurs")):
        target = matched if matched else services
        items = "\n".join(
            f"• {s['name']} — {_format_sum(s['price_uzs'])} ({s['duration_min']} daq.)"
            for s in target
        )
        return (
            f"{profile.get('name', 'Biznesimiz')} xizmatlari va narxlari:\n{items}\n\n"
            "Qaysi xizmatni tanlaysiz? Pastdagi forma orqali 10 soniyada band qilishingiz mumkin."
        )

    if any(k in msg for k in ("vaqt", "soat", "qachon", "ochiq", "manzil", "qayer", "lokatsiya", "telefon")):
        return (
            f"Ish vaqtimiz: {profile.get('hours', '')}.\n"
            f"Manzil: {profile.get('address', '')}.\n"
            f"Aloqa uchun: {profile.get('phone', '')}."
        )

    if any(k in msg for k in ("bron", "buyurtma", "yozil", "zakaz", "band")):
        first = services[0]["name"] if services else "xizmat"
        return (
            f"Albatta! Hoziroq '{first}' yoki boshqa xizmatga yozilishingiz mumkin. "
            "Chap tarafdagi buyurtma formasiga ismingiz, telefon raqamingiz va qulay vaqtni kiriting — "
            "buyurtmangiz darhol Admin CRM paneliga tushadi."
        )

    if matched:
        s = matched[0]
        return (
            f"'{s['name']}' xizmati narxi {_format_sum(s['price_uzs'])}, davomiyligi {s['duration_min']} daqiqa. "
            f"{s['description']}. Band qilish uchun buyurtma formasidan foydalaning!"
        )

    return (
        f"Assalomu alaykum! Men {profile.get('name', '')} AI yordamchisiman. "
        "Sizga xizmat narxlari, ish vaqti, manzil yoki onlayn buyurtma berishda yordam beraman. "
        "Masalan: 'Narxlar qancha?' yoki 'Manzil qayerda?' deb yozib ko'ring."
    )


def generate_ai_reply(user_message: str, state: dict[str, Any]) -> dict[str, str]:
    """Return an AI response along with the engine mode used ('gemini' or 'local')."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        context = _build_context(state)
        gemini_text = _call_gemini(user_message, context, api_key)
        if gemini_text:
            return {"reply": gemini_text, "mode": "gemini"}

    return {"reply": _local_fallback_reply(user_message, state), "mode": "local"}
