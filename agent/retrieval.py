"""
Premise & Lemma Retrieval for AI-Maths-Researcher.
Queries Loogle (type-based search) and LeanSearch (semantic search) to prevent LLM hallucinations.
"""

import urllib.request
import urllib.parse
import json
import re
from dataclasses import dataclass
from typing import List, Optional, Set

@dataclass
class Premise:
    name: str
    type_sig: str
    module: Optional[str] = None
    source: str = "loogle"

    def format_line(self) -> str:
        return f"-- {self.name} : {self.type_sig}"

class PremiseRetriever:
    def __init__(self, timeout_sec: int = 5):
        self.timeout_sec = timeout_sec

    def query_loogle(self, query: str, limit: int = 10) -> List[Premise]:
        """Queries Loogle API for type and signature matches."""
        try:
            url = f"https://loogle.lean-lang.org/json?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={"User-Agent": "AI-Maths-Researcher/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                hits = data.get("hits", [])
                premises = []
                for h in hits[:limit]:
                    name = h.get("name", "")
                    t_sig = h.get("type", "").replace("\n", " ")
                    mod = h.get("module")
                    if name:
                        premises.append(Premise(name=name, type_sig=t_sig, module=mod, source="loogle"))
                return premises
        except Exception:
            return []

    def retrieve_for_statement(self, statement: str, max_results: int = 15) -> List[Premise]:
        """
        Extracts key patterns/keywords from theorem statement and queries retrieval APIs.
        """
        results: List[Premise] = []
        seen_names: Set[str] = set()

        # 1. Identify expressions like (a ^ 2), (Even _), (0 ≤ _), etc.
        queries = []
        
        # Clean theorem signature
        cleaned = re.sub(r"/--.*?--/", "", statement, flags=re.DOTALL)
        
        # Search for equality/inequality forms
        if "≤" in cleaned or "<" in cleaned:
            queries.append("0 ≤ _ ^ 2")
            queries.append("_ ≤ _ ^ 2 + _ ^ 2")
        if "Even" in cleaned or "Odd" in cleaned:
            queries.append("Even (_ ^ 2)")
            queries.append("Even (_ + _)")
        if "%" in cleaned or "mod" in cleaned:
            queries.append("(_ + _) % _")
            queries.append("(_ ^ 2) % _")

        # Fallback keyword extraction
        words = re.findall(r"\b[a-zA-Z_]{4,}\b", cleaned)
        for w in words[:2]:
            if w not in {"theorem", "lemma", "where", "have", "intro", "exact"}:
                queries.append(w)

        for q in queries[:4]:
            hits = self.query_loogle(q, limit=5)
            for h in hits:
                if h.name not in seen_names:
                    seen_names.add(h.name)
                    results.append(h)
                    if len(results) >= max_results:
                        break
            if len(results) >= max_results:
                break

        return results

    @staticmethod
    def format_prompt_block(premises: List[Premise]) -> str:
        if not premises:
            return ""
        lines = [
            "### Relevant Verified Mathlib Lemmas (Use these exact identifiers):"
        ]
        for p in premises:
            lines.append(f"- `{p.name}` : `{p.type_sig}`")
        return "\n".join(lines)
