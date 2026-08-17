# -*- coding: utf-8 -*-
"""
طبقة البيانات: تحميل قاعدة البيانات السريرية المدمجة مع التطبيق، إدارة
الحالات المخصصة اللي بيضيفها المستخدم (تُحفظ محليًا وتُدمج مع القاعدة
الأساسية عند البحث)، ومحرك بحث مطابق تمامًا لخوارزمية البحث الأصلية
(نفس الأوزان، نفس المرادفات، نفس التطابق الضبابي لتصحيح الأخطاء الإملائية).
"""

import json
import os
import re
import uuid

APP_DATA_DIR = None  # يُهيّأ في init_paths()
CUSTOM_CASES_FILE = None
BUILTIN_DB_FILE = os.path.join(os.path.dirname(__file__), "data", "clinical_database.json")
MODES_FILE = os.path.join(os.path.dirname(__file__), "data", "modes_encyclopedia.json")


def init_paths():
    """يجب استدعاؤها بعد تشغيل التطبيق (App.user_data_dir متاح وقتها فقط)."""
    global APP_DATA_DIR, CUSTOM_CASES_FILE
    from kivy.app import App  # استيراد مؤجل حتى يمكن اختبار هذا الملف بدون Kivy مثبتة
    app = App.get_running_app()
    APP_DATA_DIR = app.user_data_dir if app else "."
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    CUSTOM_CASES_FILE = os.path.join(APP_DATA_DIR, "custom_cases.json")


# ---------------------------------------------------------------------------
# تحميل / حفظ
# ---------------------------------------------------------------------------

_builtin_cache = None
_modes_cache = None


def load_builtin_database():
    global _builtin_cache
    if _builtin_cache is None:
        with open(BUILTIN_DB_FILE, encoding="utf-8") as f:
            _builtin_cache = json.load(f)
    return _builtin_cache


def load_modes_encyclopedia():
    global _modes_cache
    if _modes_cache is None:
        with open(MODES_FILE, encoding="utf-8") as f:
            _modes_cache = json.load(f)
    return _modes_cache


def load_custom_cases():
    if not CUSTOM_CASES_FILE or not os.path.exists(CUSTOM_CASES_FILE):
        return []
    try:
        with open(CUSTOM_CASES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_custom_cases(cases):
    if not CUSTOM_CASES_FILE:
        init_paths()
    with open(CUSTOM_CASES_FILE, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)


def all_cases():
    """القاعدة الأساسية + حالات المستخدم المخصصة، جاهزة للبحث والعرض."""
    return load_builtin_database() + load_custom_cases()


# ---------------------------------------------------------------------------
# إدارة الحالات المخصصة (إضافة / تعديل / حذف)
# ---------------------------------------------------------------------------

def add_custom_case(fields):
    cases = load_custom_cases()
    new_case = dict(fields)
    new_case["id"] = uuid.uuid4().hex[:12]
    new_case["custom"] = True
    cases.append(new_case)
    save_custom_cases(cases)
    return new_case


def update_custom_case(case_id, fields):
    cases = load_custom_cases()
    for i, c in enumerate(cases):
        if c.get("id") == case_id:
            merged = dict(c)
            merged.update(fields)
            merged["id"] = case_id
            merged["custom"] = True
            cases[i] = merged
            save_custom_cases(cases)
            return merged
    return None


def delete_custom_case(case_id):
    cases = load_custom_cases()
    cases = [c for c in cases if c.get("id") != case_id]
    save_custom_cases(cases)


def get_custom_case(case_id):
    for c in load_custom_cases():
        if c.get("id") == case_id:
            return c
    return None


def clear_all_custom_cases():
    save_custom_cases([])


# ---------------------------------------------------------------------------
# محرك البحث (منقول بالكامل من منطق JS الأصلي في التطبيق)
# ---------------------------------------------------------------------------

SEARCH_SYNONYMS = {
    "خشونه": ["التهاب المفصل", "استيوارثرايتس", "osteoarthritis", "oa"],
    "الركبه": ["ركبه", "knee"],
    "الرقبه": ["رقبه", "عنق", "neck", "cervical"],
    "الظهر": ["ظهر", "عمود فقري", "back", "spine"],
    "الكتف": ["كتف", "shoulder"],
    "عرق النسا": ["نسا", "sciatica", "وجع النسا"],
    "انزلاق غضروفي": ["ديسك", "disc", "غضروف"],
    "شلل": ["فالج", "paralysis", "palsy"],
    "جلطه": ["سكته دماغيه", "stroke", "cva"],
    "تنميل": ["خدر", "numbness", "tingling"],
    "الم": ["وجع", "الآم", "pain", "وجعا"],
    "تورم": ["انتفاخ", "swelling", "edema"],
    "تشنج": ["تقلص", "spasm", "cramp"],
    "ضعف": ["ضمور", "weakness", "atrophy"],
    "التهاب": ["الم مزمن", "inflammation", "itis"],
    "كسر": ["فراكشر", "fracture"],
    "سكري": ["سكر", "diabetes", "diabetic"],
    "بعد الولاده": ["نفاس", "postpartum", "postnatal"],
    "الكوع": ["مرفق", "elbow", "تنس البو"],
    "القدم": ["كف القدم", "foot"],
    "الكاحل": ["ankle", "التواء"],
    "الفخذ": ["thigh", "hip femoral"],
    "الورك": ["مفصل الحوض", "hip"],
}


def normalize_text(text):
    text = (text or "").lower()
    text = re.sub(r"[أإآ]", "ا", text)
    text = text.replace("ة", "ه")
    text = text.replace("ى", "ي")
    return text


def expand_with_synonyms(terms):
    expanded = set(terms)
    for term in terms:
        for key, syns in SEARCH_SYNONYMS.items():
            if key in term or term in key:
                expanded.update(syns)
                expanded.add(key)
            for s in syns:
                if s in term or term in s:
                    expanded.add(key)
                    expanded.update(syns)
    return list(expanded)


def levenshtein(a, b):
    if a == b:
        return 0
    al, bl = len(a), len(b)
    if al == 0:
        return bl
    if bl == 0:
        return al
    dp = [[0] * (bl + 1) for _ in range(al + 1)]
    for i in range(al + 1):
        dp[i][0] = i
    for j in range(bl + 1):
        dp[0][j] = j
    for i in range(1, al + 1):
        for j in range(1, bl + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[al][bl]


def fuzzy_includes(haystack_words, term):
    # نسمح بخطأ إملائي واحد فقط للكلمات الأطول من 3 أحرف
    if len(term) <= 3:
        return False
    max_dist = 2 if len(term) > 6 else 1
    for w in haystack_words:
        if abs(len(w) - len(term)) <= max_dist and levenshtein(w, term) <= max_dist:
            return True
    return False


def get_general_safety_note(mode_str):
    mode_str = mode_str or ""
    is_ems = "EMS" in mode_str
    is_tens = "TENS" in mode_str
    notes = []
    if is_ems or is_tens:
        notes.append("لا يُستخدم فوق منظم ضربات القلب (Pacemaker) أو أي جهاز كهربائي مزروع.")
        notes.append("يُمنع وضع الأقطاب على الجزء الأمامي من الرقبة (الجيب السباتي) أو الصدر بشكل متقاطع، أو منطقة الرأس والعينين.")
        notes.append("يُمنع الاستخدام فوق الجروح المفتوحة، الجلد المصاب، أو مناطق الأورام، أو أثناء الحمل فوق منطقة البطن والحوض دون استشارة.")
    if is_ems:
        notes.append("EMS يُحدث انقباضاً عضلياً فعلياً؛ ابدأ بشدة منخفضة وزدها تدريجياً حسب تحمل المريض.")
    return notes


def score_item(item, raw_keyword, raw_terms):
    normalized_title = normalize_text(item.get("title", ""))
    normalized_mode = normalize_text(item.get("mode", ""))
    normalized_explanation = normalize_text(item.get("explanation", ""))
    normalized_keywords = [normalize_text(k) for k in item.get("keywords", [])]
    title_words = normalized_title.split()
    keyword_words = [w for k in normalized_keywords for w in k.split()]

    score = 0
    matched_terms = 0

    if raw_keyword in normalized_keywords:
        score += 1000

    for raw_term in raw_terms:
        variants = [normalize_text(v) for v in expand_with_synonyms([raw_term])]
        term_matched = False
        for term in variants:
            if any(term in k for k in normalized_keywords):
                score += 50
                term_matched = True
            if term in normalized_title:
                score += 20
                term_matched = True
            if term in normalized_mode:
                score += 10
                term_matched = True
            if term in normalized_explanation:
                score += 3
                term_matched = True
        if not term_matched:
            if fuzzy_includes(keyword_words, raw_term):
                score += 25
                term_matched = True
            elif fuzzy_includes(title_words, raw_term):
                score += 12
                term_matched = True
        if term_matched:
            matched_terms += 1

    return score, matched_terms


def search(raw_keyword, cases=None):
    """
    يرجع (matched_items, is_fallback) - قائمة الحالات الأعلى تطابقًا فقط
    (نفس منطق "أعلى نتيجة" في التطبيق الأصلي، وليس كل نتيجة جزئية).
    """
    raw_keyword = (raw_keyword or "").strip()
    if not raw_keyword:
        return [], False

    if cases is None:
        cases = all_cases()

    normalized_keyword = normalize_text(raw_keyword)
    raw_terms = [t for t in normalized_keyword.split(" ") if len(t) > 1]
    if not raw_terms:
        raw_terms = [normalized_keyword]

    scored = []
    for item in cases:
        s, m = score_item(item, normalized_keyword, raw_terms)
        scored.append((item, s, m))

    candidates = [t for t in scored if t[2] == len(raw_terms) and t[1] > 0]
    is_fallback = False

    if not candidates:
        is_fallback = True
        min_terms_covered = max(1, -(-len(raw_terms) * 6 // 10))  # ceil(len*0.6)
        candidates = [t for t in scored if t[2] >= min_terms_covered and t[1] >= 15]

    candidates.sort(key=lambda t: t[1], reverse=True)

    if not candidates:
        return [], is_fallback

    top_score = candidates[0][1]
    matched = [t[0] for t in candidates if t[1] == top_score]
    return matched, is_fallback


def extract_english_term(title):
    m = re.search(r"\(([^)]+)\)\s*$", title or "")
    return m.group(1) if m else None
