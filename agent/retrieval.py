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

    def query_leansearch(self, query: str, limit: int = 5) -> List[Premise]:
        """Queries LeanSearch API for semantic Mathlib retrieval."""
        try:
            url = "https://leansearch.net/search"
            payload = {"query": [query], "num_results": limit}
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "AI-Maths-Researcher/1.0"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                premises = []
                if isinstance(data, list) and data and isinstance(data[0], list):
                    for item in data[0][:limit]:
                        res = item.get("result", {})
                        raw_name = res.get("name", [])
                        name = ".".join(raw_name) if isinstance(raw_name, list) else str(raw_name)
                        sig = res.get("signature", "") or res.get("type", "")
                        mod_list = res.get("module_name", [])
                        mod = ".".join(mod_list) if isinstance(mod_list, list) else str(mod_list)
                        if name:
                            premises.append(Premise(name=name, type_sig=sig.replace("\n", " "), module=mod, source="leansearch"))
                return premises
        except Exception:
            return []

    def query_for_goal(self, goal_str: str, limit: int = 5) -> List[Premise]:
        """Extracts goal target after ⊢ and queries Loogle and LeanSearch."""
        # Find conclusion target after turnstile ⊢
        target = ""
        for line in goal_str.splitlines():
            if "⊢" in line:
                target = line.split("⊢", 1)[1].strip()
                break
        if not target:
            return []

        premises = []
        # 1. Semantic query via LeanSearch on the goal target
        premises.extend(self.query_leansearch(target, limit=limit))

        # 2. Pattern query on Loogle
        clean_pattern = re.sub(r"\b[a-zA-Z0-9_']+\b", "_", target)
        if len(clean_pattern) > 3 and clean_pattern != target:
            premises.extend(self.query_loogle(clean_pattern, limit=3))

        return premises[:limit]

    def query_for_unknown_identifier(self, identifier: str, limit: int = 5) -> List[Premise]:
        """Finds candidate Mathlib lemmas when a model hallucinates an identifier."""
        clean_id = identifier.split(".")[-1]
        results = self.query_leansearch(clean_id, limit=limit)
        if not results:
            results = self.query_loogle(clean_id, limit=limit)
        return results

    def retrieve_for_statement(self, statement: str, max_results: int = 15) -> List[Premise]:
        """
        Combines LeanSearch semantic search with Loogle type-based search.
        """
        results: List[Premise] = []
        seen_names: Set[str] = set()

        # 1. LeanSearch semantic retrieval with clean statement text
        clean_stmt = re.sub(r"/--.*?--/", "", statement, flags=re.DOTALL)
        clean_stmt = re.sub(r":=\s*by.*$", "", clean_stmt, flags=re.DOTALL).strip()
        leansearch_hits = self.query_leansearch(clean_stmt, limit=6)
        for h in leansearch_hits:
            if h.name not in seen_names:
                seen_names.add(h.name)
                results.append(h)

        # 2. Loogle queries for specific mathematical expressions
        queries = []
        if "≤" in clean_stmt or "<" in clean_stmt:
            queries.append("0 ≤ _ ^ 2")
            queries.append("_ ≤ _ ^ 2 + _ ^ 2")
        if "Even" in clean_stmt or "Odd" in clean_stmt:
            queries.append("Even (_ ^ 2)")
            queries.append("Even (_ + _)")
        if "%" in clean_stmt or "mod" in clean_stmt:
            queries.append("(_ + _) % _")
            queries.append("(_ ^ 2) % _")
        if "Real.log" in clean_stmt or "log" in clean_stmt:
            queries.append("Real.log (_ * _)")
            queries.append("Real.log_pos")

        for q in queries[:4]:
            hits = self.query_loogle(q, limit=4)
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
            "### Relevant Verified Mathlib Lemmas (Use these exact identifiers and modules):"
        ]
        for p in premises:
            mod_info = f" (import {p.module})" if p.module else ""
            lines.append(f"- `{p.name}` : `{p.type_sig}`{mod_info}")
        return "\n".join(lines)
