"""Developlus API - Dataset Service

TSDS (Tech Stack Dataset) ve TDS (Technology Dataset) verilerini yukler
ve kullanicinin sorgu + anket verilerine gore ilgili parcalari bulur.

Dosyalar:
  - tsds-final.json: Gercek sirket tech stack leri (Uber, Netflix vb.)
  - tds-prefinal.json: Bireysel arac profilleri (React, PostgreSQL vb.)
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─── Dataset Yukleme ─────────────────────────────────────────────────────────

_BASE = Path(__file__).parent.parent / "datasets"


def _load_json(filename: str) -> list:
    path = _BASE / filename
    if not path.exists():
        print(f"[dataset_service] Dataset bulunamadi: {path}")
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[dataset_service] JSON parse hatasi ({filename}): {e}")
        return []


_TSDS: List[Dict[str, Any]] = _load_json("tsds-final.json")
_TDS: List[Dict[str, Any]] = _load_json("tds-prefinal.json")

print(f"[dataset_service] TSDS: {len(_TSDS)} sirket, TDS: {len(_TDS)} arac yuklendi")


# ─── Keyword ve Endustri Eslestirme ──────────────────────────────────────────

_TECH_KEYWORDS = {
    # Frontend
    "react", "vue", "angular", "svelte", "nextjs", "next.js", "nuxt",
    "typescript", "javascript", "tailwind",
    # Backend
    "python", "node", "nodejs", "fastapi", "django", "flask", "express",
    "go", "golang", "rust", "java", "spring", "dotnet", ".net", "php", "laravel",
    "ruby", "rails",
    # Database
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "sqlite", "cassandra", "dynamodb", "supabase", "firebase", "neo4j",
    "clickhouse", "snowflake",
    # Infrastructure
    "docker", "kubernetes", "aws", "gcp", "azure", "nginx", "kafka", "rabbitmq",
    "terraform", "ansible", "jenkins", "github actions", "circleci",
    # Industry
    "e-commerce", "ecommerce", "fintech", "finance", "saas", "social", "streaming",
    "marketplace", "healthcare", "edtech", "gaming", "startup",
    # Scale
    "startup", "small", "medium", "enterprise", "large", "scale", "scalability",
    # Features
    "realtime", "real-time", "microservice", "monolith", "serverless", "mobile",
    "ai", "ml", "machine learning",
}

_INDUSTRY_MAP = {
    "e-commerce": ["e-commerce", "ecommerce", "shop", "store", "marketplace"],
    "finance": ["finance", "fintech", "bank", "payment", "crypto", "trading"],
    "social": ["social", "community", "network", "chat", "messaging"],
    "streaming": ["streaming", "video", "music", "audio", "entertainment", "media"],
    "delivery": ["delivery", "food", "logistics", "transportation", "ride"],
    "saas": ["saas", "b2b", "enterprise", "platform", "tool", "api"],
    "education": ["education", "edtech", "learning", "course", "school"],
    "healthcare": ["health", "medical", "clinic", "hospital"],
    "gaming": ["game", "gaming", "esports"],
}


def _extract_keywords(text: str) -> List[str]:
    """Metinden tech keyword lerini cikarir."""
    text_lower = text.lower()
    found = []
    for kw in _TECH_KEYWORDS:
        if kw in text_lower:
            found.append(kw)
    return found


def _detect_industry(text: str) -> List[str]:
    """Metinden endustri kategorilerini tespit eder."""
    text_lower = text.lower()
    detected = []
    for industry, terms in _INDUSTRY_MAP.items():
        if any(t in text_lower for t in terms):
            detected.append(industry)
    return detected


# ─── Sirket Stack Arama ───────────────────────────────────────────────────────

def search_company_stacks(
    query: str,
    survey_context: Optional[str] = None,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Kullanicinin sorusu + anket verilerine gore benzer sirket stacklerini bulur.
    Skor = keyword eslesmesi + endustri eslesmesi
    """
    combined_text = query + " " + (survey_context or "")
    query_keywords = set(_extract_keywords(combined_text))
    query_industries = set(_detect_industry(combined_text))

    scored: List[tuple] = []
    for company in _TSDS:
        score = 0
        industry = company.get("industry", "").lower()
        stack = company.get("stack_architecture", {})

        # Tum stack teknolojilerini duz listeye cevir
        all_techs: set = set()
        for layer_techs in stack.values():
            if isinstance(layer_techs, list):
                for t in layer_techs:
                    all_techs.add(str(t).lower())

        # Keyword eslesmesi
        for kw in query_keywords:
            if any(kw in tech for tech in all_techs):
                score += 2
            if kw in industry:
                score += 3

        # Endustri eslesmesi
        for ind in query_industries:
            if ind in industry:
                score += 4

        if score > 0:
            scored.append((score, company))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:max_results]]


# ─── Arac Profili Arama ───────────────────────────────────────────────────────

def search_tool_profiles(
    query: str,
    max_results: int = 8,
) -> List[Dict[str, Any]]:
    """
    Kullanicinin sorusuna gore alakali arac profillerini bulur.
    tds-prefinal.json dan verisi dolu kayitlari doner.
    """
    query_keywords = set(_extract_keywords(query))
    query_lower = query.lower()

    matched: List[tuple] = []
    for tool in _TDS:
        slug = tool.get("slug", "").lower()
        display_name = tool.get("display_name", "").lower()
        intel = tool.get("core_intel", {})
        description = intel.get("description", "").lower() if isinstance(intel, dict) else ""
        tags = [str(t).lower() for t in (intel.get("tags", []) if isinstance(intel, dict) else [])]
        criteria = tool.get("matching_criteria", {})
        best_for = [str(b).lower() for b in (criteria.get("best_for", []) if isinstance(criteria, dict) else [])]

        # Veri dolu mu kontrolu
        has_data = bool(description) or bool(tags) or bool(best_for)
        if not has_data:
            continue

        # Eslesme skoru
        score = 0
        if slug in query_lower or display_name in query_lower:
            score += 10
        for kw in query_keywords:
            if kw in slug or kw in display_name:
                score += 5
            if kw in description:
                score += 2
            if any(kw in t for t in tags):
                score += 3
            if any(kw in b for b in best_for):
                score += 3

        if score > 0:
            matched.append((score, tool))

    matched.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in matched[:max_results]]


# ─── Context Builder ─────────────────────────────────────────────────────────

def build_dataset_context(
    query: str,
    survey_context: Optional[str] = None,
) -> Optional[str]:
    """
    Soru + anket verilerine gore veri setlerinden bir RAG context metni olusturur.
    Hicbir sey bulunamazsa None doner (Tavily fallback icin sinyal).
    """
    parts: List[str] = []

    # 1. Benzer sirket stackleri
    companies = search_company_stacks(query, survey_context, max_results=4)
    if companies:
        company_section = "## Gercek Dunya Sirket Stack Ornekleri\n"
        for c in companies:
            stack = c.get("stack_architecture", {})
            layers = []
            for layer_name, techs in stack.items():
                if techs and isinstance(techs, list):
                    layers.append(f"  - **{layer_name}**: {', '.join(str(t) for t in techs)}")
            if not layers:
                continue
            company_section += (
                f"\n### {c.get('company_name')} ({c.get('industry')})\n"
                f"{c.get('description', '')}\n"
                + "\n".join(layers)
                + "\n"
            )
        parts.append(company_section)

    # 2. Ilgili arac profilleri (yalnizca verisi doluysa)
    tools = search_tool_profiles(query, max_results=6)
    if tools:
        tool_section = "## Ilgili Teknoloji Profilleri\n"
        for t in tools:
            intel = t.get("core_intel", {}) or {}
            criteria = t.get("matching_criteria", {}) or {}
            desc = intel.get("description", "") if isinstance(intel, dict) else ""
            tags = intel.get("tags", []) if isinstance(intel, dict) else []
            best_for = criteria.get("best_for", []) if isinstance(criteria, dict) else []
            learning = criteria.get("learning_curve", "") if isinstance(criteria, dict) else ""
            scalability = criteria.get("scalability_tier", "") if isinstance(criteria, dict) else ""

            tool_section += f"\n### {t.get('display_name')} (`{t.get('slug')}`)\n"
            if desc:
                tool_section += f"{desc}\n"
            if tags:
                tool_section += f"- **Etiketler:** {', '.join(str(x) for x in tags)}\n"
            if best_for:
                tool_section += f"- **En iyi oldugu yer:** {', '.join(str(x) for x in best_for)}\n"
            if learning:
                tool_section += f"- **Ogrenme egrisi:** {learning}\n"
            if scalability:
                tool_section += f"- **Olceklenebilirlik:** {scalability}\n"
        parts.append(tool_section)

    if not parts:
        return None

    return "\n\n".join(parts)
