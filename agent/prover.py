"""
Autonomous Proof Search & Repair Engine for AI-Maths-Researcher.
Implements Strategy A (Whole Proof Generation + Goal State Repair + pass@k).
Integrates LeanREPL for 50ms verification, Loogle premise retrieval, and SQLite tracking.
"""

import os
import re
import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from agent.repl_client import LeanREPL, REPLResponse
from agent.verifier import RemoteProdVerifier, VerificationResult
from agent.retrieval import PremiseRetriever, Premise
from agent.db import AttemptsDB

@dataclass
class ProverConfig:
    max_attempts: int = 6
    budget_usd: float = 1.00
    model: str = "gemini-2.5-flash"
    temperature: float = 0.2
    timeout_per_attempt_sec: int = 15

class LLMProvider:
    """Dispatches requests to Gemini, DeepSeek, or OpenAI based on available keys."""
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")

    def generate(self, prompt: str, theorem_decl: str, iteration: int = 1, temperature: float = 0.2) -> Tuple[str, int, int, float]:
        """
        Returns (generated_code, prompt_tokens, completion_tokens, cost_usd).
        Falls back to intelligent tactic search if no external API key is set.
        """
        if self.gemini_key:
            return self._call_gemini(prompt, temperature)
        elif self.deepseek_key:
            return self._call_deepseek(prompt, temperature)
        elif self.openai_key:
            return self._call_openai(prompt, temperature)
        else:
            return self._fallback_tactic_generator(theorem_decl, iteration)

    def _call_gemini(self, prompt: str, temperature: float) -> Tuple[str, int, int, float]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": 2048}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    text = parts[0].get("text", "")
            usage = data.get("usageMetadata", {})
            p_tok = usage.get("promptTokenCount", len(prompt) // 4)
            c_tok = usage.get("candidatesTokenCount", len(text) // 4)
            cost = (p_tok * 0.0000001) + (c_tok * 0.0000004)
            return text, p_tok, c_tok, cost

    def _call_deepseek(self, prompt: str, temperature: float) -> Tuple[str, int, int, float]:
        url = "https://api.deepseek.com/chat/completions"
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.deepseek_key}"}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            p_tok = usage.get("prompt_tokens", 0)
            c_tok = usage.get("completion_tokens", 0)
            cost = (p_tok * 0.00000014) + (c_tok * 0.00000028)
            return text, p_tok, c_tok, cost

    def _call_openai(self, prompt: str, temperature: float) -> Tuple[str, int, int, float]:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.openai_key}"}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            p_tok = usage.get("prompt_tokens", 0)
            c_tok = usage.get("completion_tokens", 0)
            cost = (p_tok * 0.00000015) + (c_tok * 0.0000006)
            return text, p_tok, c_tok, cost

    def _fallback_tactic_generator(self, theorem_decl: str, iteration: int) -> Tuple[str, int, int, float]:
        """Algorithmic tactic exploration trying standard Mathlib automation tactics."""
        tactics_ladder = [
            "by\n  subst_vars\n  norm_num at *",
            "by\n  omega",
            "by\n  ring",
            "by\n  linarith",
            "by\n  nlinarith",
            "by\n  aesop",
            "by\n  intros; subst_vars; norm_num at *",
            "by\n  intros; ring",
            "by\n  intros; omega",
        ]
        chosen = tactics_ladder[(iteration - 1) % len(tactics_ladder)]
        code = f"{theorem_decl} := {chosen}"
        return f"```lean\n{code}\n```", len(theorem_decl)//4, len(code)//4, 0.0

class ProofSearchEngine:
    def __init__(self, config: ProverConfig = ProverConfig()):
        self.config = config
        self.llm = LLMProvider(model=config.model)
        self.retriever = PremiseRetriever()
        self.verifier = RemoteProdVerifier()
        self.db = AttemptsDB()

    def sanitize_code(self, raw_text: str, theorem_decl: str) -> str:
        """Extracts code from markdown code fences and guarantees a valid theorem structure."""
        matches = re.findall(r"```lean(.*?)```", raw_text, re.DOTALL)
        code = matches[-1].strip() if matches else raw_text.strip()

        # If model only provided proof block (by ...)
        if "theorem" not in code and "lemma" not in code:
            code = f"{theorem_decl} := {code}"

        # Guarantee standard Mathlib imports
        if not code.startswith("import"):
            code = "import Mathlib.Tactic\nimport Mathlib.Algebra.Ring.Parity\n\nset_option linter.style.header false\n\n" + code

        return code

    def build_prompt(
        self,
        theorem_decl: str,
        premises: List[Premise],
        history: List[Dict[str, Any]]
    ) -> str:
        prompt_parts = [
            "You are an expert Lean 4 and Mathlib formal mathematician.",
            "Your goal is to write a complete, self-contained Lean 4 proof for the given theorem statement.",
            "CRITICAL RULES:",
            "1. Output ONLY valid Lean 4 code inside a ```lean ... ``` code block.",
            "2. Do NOT use `sorry` or unofficial axioms.",
            "3. Use standard Mathlib tactics: `omega`, `ring`, `linarith`, `nlinarith`, `aesop`, `subst_vars`, `norm_num`, `rcases`, `have`, `calc`, `rw`, `exact?`.",
            "4. Include all necessary Mathlib imports at the top.\n",
            f"### Target Theorem Declaration:\n```lean\n{theorem_decl}\n```\n"
        ]

        if premises:
            prompt_parts.append(self.retriever.format_prompt_block(premises) + "\n")

        if history:
            prompt_parts.append("### Previous Attempt Diagnostics (Fix these errors):")
            for h in history[-2:]:
                prompt_parts.append(f"- Failed Code:\n```lean\n{h['code']}\n```")
                if h.get("errors"):
                    prompt_parts.append(f"- Compiler Errors: {h['errors']}")
                if h.get("goals"):
                    prompt_parts.append(f"- Unsolved Goal State:\n{h['goals']}\n")

        prompt_parts.append("Provide the complete, corrected Lean 4 code:")
        return "\n".join(prompt_parts)

    def prove_theorem(self, theorem_decl: str, problem_name: str = "Candidate") -> Tuple[bool, str]:
        print(f"\n🧠 Lancement de la recherche de preuve pour '{problem_name}'...")
        print(f"Énoncé : {theorem_decl.strip().splitlines()[0]}")

        # 1. Retrieve Mathlib premises via Loogle
        print("🔍 Récupération des lemmes Mathlib via Loogle...")
        premises = self.retriever.retrieve_for_statement(theorem_decl)
        if premises:
            print(f"  → {len(premises)} lemmes pertinents récupérés.")

        history: List[Dict[str, Any]] = []
        total_cost = 0.0

        with LeanREPL() as repl:
            for iteration in range(1, self.config.max_attempts + 1):
                if total_cost >= self.config.budget_usd:
                    print(f"⚠️ Budget limite de ${self.config.budget_usd:.2f} atteint. Arrêt.")
                    break

                prompt = self.build_prompt(theorem_decl, premises, history)
                print(f"\n[Tentative {iteration}/{self.config.max_attempts}] Génération de preuve...")

                # Call LLM / tactic engine
                raw_llm, p_tok, c_tok, cost = self.llm.generate(
                    prompt,
                    theorem_decl=theorem_decl,
                    iteration=iteration,
                    temperature=self.config.temperature
                )
                total_cost += cost

                candidate_code = self.sanitize_code(raw_llm, theorem_decl)

                # Level 1 Verification (REPL in ~50ms)
                print(f"  ⚡ Test rapide via LeanREPL...")
                repl_resp = repl.check_code(candidate_code)

                if repl_resp.is_success:
                    print(f"  ✨ REPL validé en {repl_resp.duration_ms:.1f}ms ! Envoi au Juge Final (LXC Prod)...")
                    
                    # Level 2 Verification (LXC Prod: lake env lean + #print axioms audit)
                    prod_res = self.verifier.verify_file_content(candidate_code, temp_name=f"{problem_name}.lean")
                    
                    # Record in DB
                    self.db.record_attempt(
                        problem_name=problem_name,
                        iteration=iteration,
                        model=self.config.model,
                        prompt=prompt,
                        candidate_code=candidate_code,
                        success=prod_res.success,
                        compiler_errors=prod_res.error_message,
                        duration_ms=repl_resp.duration_ms,
                        prompt_tokens=p_tok,
                        completion_tokens=c_tok,
                        cost_usd=cost
                    )

                    if prod_res.success:
                        print(f"  🏆 PREUVE CERTIFIÉE SANS FAUTE en {iteration} itération(s) !")
                        return True, candidate_code
                    else:
                        print(f"  ⚠️ Rejet Juge Final : {prod_res.error_message}")
                        history.append({
                            "code": candidate_code,
                            "errors": prod_res.error_message,
                            "goals": ""
                        })
                else:
                    err_text = "\n".join(repl_resp.error_texts)
                    goal_text = "\n".join(repl_resp.goals)
                    print(f"  ❌ Échec REPL ({repl_resp.duration_ms:.1f}ms) : {err_text[:120]}...")

                    # Record in DB
                    self.db.record_attempt(
                        problem_name=problem_name,
                        iteration=iteration,
                        model=self.config.model,
                        prompt=prompt,
                        candidate_code=candidate_code,
                        success=False,
                        compiler_errors=err_text,
                        unsolved_goals=goal_text,
                        duration_ms=repl_resp.duration_ms,
                        prompt_tokens=p_tok,
                        completion_tokens=c_tok,
                        cost_usd=cost
                    )

                    history.append({
                        "code": candidate_code,
                        "errors": err_text,
                        "goals": goal_text
                    })

        print(f"\n❌ Échec : preuve non trouvée après {self.config.max_attempts} tentatives.")
        return False, ""
