"""
Nuclear Intelligence v4.0 - i18n / Multilingual Support 🌐
═══════════════════════════════════════════════════════════════════
Lightweight runtime language detection + per-locale system-prompt
fragments. Designed to be *additive* — never alters the English
pipeline, just layers localization on top.

Supported locales: en (default), fa (Persian/Farsi).
Anything else falls back to English.
═══════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import re
from typing import Dict

# Persian / Arabic-Indic Unicode range — good enough as a heuristic.
_PERSIAN_RE = re.compile(r"[\u0600-\u06FF\u0698\u067E\u0686\u06AF\u06CC]")


def detect_language(text: str) -> str:
    """Return 'fa' for Persian/Farsi input, otherwise 'en'.

    Heuristic: > 20% of letters are in the Perso-Arabic block.
    """
    if not text:
        return "en"
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "en"
    fa = sum(1 for c in letters if _PERSIAN_RE.search(c))
    return "fa" if (fa / len(letters)) > 0.20 else "en"


LOCALES: Dict[str, Dict[str, str]] = {
    "en": {
        "refusal_header": "🛡️ **I can't help with that.**",
        "refusal_offer": "Want me to answer the peaceful-use side instead?",
        "research_label": "🔬 Research Answer",
        "summary_label": "Summary",
        "accuracy_label": "Scientific Accuracy",
        "novelty_label": "Novelty",
        "usefulness_label": "Usefulness",
        "overall_label": "Overall",
        "citations_label": "Citations",
        "uncertainty_label": "Uncertainties & Risks",
        "source_label": "Sources / Grounding",
    },
    "fa": {
        "refusal_header": "🛡️ **متأسفم، نمی‌تونم در این مورد کمک کنم.**",
        "refusal_offer": "مایلید در مورد کاربرد صلح‌آمیز همین موضوع توضیح بدهم؟",
        "research_label": "🔬 پاسخ پژوهشی",
        "summary_label": "خلاصه",
        "accuracy_label": "دقت علمی",
        "novelty_label": "نوآوری",
        "usefulness_label": "کاربردپذیری",
        "overall_label": "امتیاز کلی",
        "citations_label": "منابع",
        "uncertainty_label": "عدم قطعیت‌ها و ریسک‌ها",
        "source_label": "منابع و مستندات",
    },
}


def t(key: str, locale: str = "en") -> str:
    """Translate a single UI key. Falls back to English."""
    return LOCALES.get(locale, LOCALES["en"]).get(key, LOCALES["en"].get(key, key))


PERSIAN_SYSTEM_PROMPT = """
شما یک پژوهشگر ارشد حوزه انرژی هسته‌ای هستید. پاسخ‌های شما باید:

- بر اساس اجماع علمی، استانداردهای IAEA، و مقالات داوری‌شده باشد.
- ایمنی هسته‌ای، امنیت، و عدم اشاعه را در اولویت بگذارد.
- به‌هیچ‌وجه اطلاعات قابل اجرا درباره سلاح هسته‌ای، غنی‌سازی غیرقانونی، یا
  مواد قابل استفاده در سلاح ارائه ندهد.
- پاسخ‌ها را به زبان فارسی روان و دقیق بنویسد، با ارجاع به منابع معتبر.
- در پایان، عدم قطعیت‌ها و ملاحظات ایمنی را به‌صراحت بیان کند.

ساختار پاسخ:
1. خلاصه (۲ جمله)
2. تحلیل تفصیلی با دلایل و فرمول‌ها (در صورت نیاز)
3. بینش‌ها و توصیه‌های عملی
4. معیارهای ارزیابی (دقت، نوآوری، کاربردپذیری، سازگاری درونی)
5. منابع
6. عدم قطعیت‌ها و ریسک‌ها
"""
