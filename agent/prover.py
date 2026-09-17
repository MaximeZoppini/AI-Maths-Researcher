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

def load_dotenv():
    """Auto-loads environment variables from .env in project root if present."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

load_dotenv()

@dataclass
class ProverConfig:
    max_attempts: int = 6
    budget_usd: float = 1.00
    model: str = "deepseek-chat"
    temperature: float = 0.2
    dynamic_temperature: bool = True
    timeout_per_attempt_sec: int = 25
    pass_k: int = 1
    enable_escalation: bool = True

class LLMProvider:
    """Dispatches requests to DeepSeek, Gemini, or OpenAI based on available keys."""
    def __init__(self, model: Optional[str] = None):
        load_dotenv()
        self.deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        
        if model:
            self.model = model
        elif self.deepseek_key:
            self.model = "deepseek-chat"
        elif self.gemini_key:
            self.model = "gemini-2.5-flash"
        elif self.openai_key:
            self.model = "gpt-4o-mini"
        else:
            self.model = "fallback-tactic-search"

    def generate(
        self,
        prompt: str,
        theorem_decl: str,
        iteration: int = 1,
        temperature: float = 0.2,
        model: Optional[str] = None
    ) -> Tuple[str, int, int, float]:
        """
        Returns (generated_code, prompt_tokens, completion_tokens, cost_usd).
        """
        target_model = model or self.model
        if self.deepseek_key:
            return self._call_deepseek(prompt, temperature, model=target_model)
        elif self.gemini_key:
            return self._call_gemini(prompt, temperature, model=target_model)
        elif self.openai_key:
            return self._call_openai(prompt, temperature, model=target_model)
        else:
            return self._fallback_tactic_generator(theorem_decl, iteration)

    def _call_deepseek(self, prompt: str, temperature: float, model: str = "deepseek-chat") -> Tuple[str, int, int, float]:
        url = "https://api.deepseek.com/chat/completions"
        is_reasoner = (model == "deepseek-reasoner")

        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an elite formal mathematician specialized in Lean 4 and Mathlib. Output only valid Lean 4 code."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 8192 if is_reasoner else 2048
        }
        # DeepSeek reasoner does not accept temperature
        if not is_reasoner:
            payload["temperature"] = temperature

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.deepseek_key}"}
        )
        timeout_http = 120 if is_reasoner else 35
        with urllib.request.urlopen(req, timeout=timeout_http) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            choice = data["choices"][0]["message"]
            text = choice.get("content") or ""
            reasoning = choice.get("reasoning_content") or ""
            if reasoning and is_reasoner:
                print(f"    💭 DeepSeek Reasoner ({len(reasoning)} caractères de CoT)...")
            usage = data.get("usage", {})
            p_tok = usage.get("prompt_tokens", 0)
            c_tok = usage.get("completion_tokens", 0)
            if is_reasoner:
                cost = (p_tok * 0.00000055) + (c_tok * 0.00000219)
            else:
                cost = (p_tok * 0.00000014) + (c_tok * 0.00000028)
            return text, p_tok, c_tok, cost

    def _call_gemini(self, prompt: str, temperature: float, model: str = "gemini-2.5-flash") -> Tuple[str, int, int, float]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}"
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

    def _call_openai(self, prompt: str, temperature: float, model: str = "gpt-4o-mini") -> Tuple[str, int, int, float]:
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
    def __init__(self, config: Optional[ProverConfig] = None):
        self.config = config or ProverConfig()
        self.llm = LLMProvider(model=self.config.model)
        self.retriever = PremiseRetriever()
        self.verifier = RemoteProdVerifier()
        self.db = AttemptsDB()

    def sanitize_code(self, raw_text: str, theorem_decl: str) -> str:
        """Extracts code from markdown code fences and guarantees a valid theorem structure."""
        matches = re.findall(r"```lean(.*?)```", raw_text, re.DOTALL)
        code = matches[-1].strip() if matches else raw_text.strip()

        if "theorem" not in code and "lemma" not in code:
            code = f"{theorem_decl} := {code}"

        # Normalize umbrella 'import Mathlib' to fast targeted imports
        code = re.sub(
            r"^\s*import\s+Mathlib\s*$",
            "import Mathlib.Tactic\nimport Mathlib.Data.Real.Basic\nimport Mathlib.Algebra.Ring.Parity",
            code,
            flags=re.MULTILINE
        )

        if not code.startswith("import"):
            code = (
                "import Mathlib.Tactic\n"
                "import Mathlib.Data.Real.Basic\n"
                "import Mathlib.Algebra.Ring.Parity\n"
                "import Mathlib.Data.Nat.Factorial.Basic\n\n"
                "open scoped Nat\n"
                "open scoped Real\n\n"
                "set_option linter.style.header false\n\n"
                + code
            )

        return code

    def build_prompt(
        self,
        theorem_decl: str,
        premises: List[Premise],
        history: List[Dict[str, Any]],
        context_code: str = ""
    ) -> str:
        prompt_parts = [
            "You are an expert Lean 4 and Mathlib formal mathematician.",
            "Your goal is to write a complete, self-contained Lean 4 proof for the given theorem statement.",
            "CRITICAL RULES:",
            "1. Output ONLY valid Lean 4 code inside a ```lean ... ``` code block.",
            "2. Do NOT use `sorry` or unofficial axioms.",
            "3. Use standard Mathlib tactics: `omega`, `ring`, `linarith`, `nlinarith`, `decide`, `aesop`, `subst_vars`, `norm_num`, `rcases`, `have`, `calc`, `rw`, `zify`, `exact?`.",
            "4. Include all necessary Mathlib imports at the top.\n",
            f"### Target Theorem Declaration:\n```lean\n{theorem_decl}\n```\n"
        ]

        if context_code:
            prompt_parts.append("### Available Lemmas in Context:\n```lean\n" + context_code.strip() + "\n```\n")

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

    def prove_theorem(
        self,
        theorem_decl: str,
        problem_name: str = "Candidate",
        context_code: str = "",
        external_repl: Optional[LeanREPL] = None
    ) -> Tuple[bool, str]:
        print(f"\n🧠 Lancement de la recherche de preuve pour '{problem_name}'...")
        print(f"Modèle actif : {self.llm.model}")
        print(f"Énoncé : {theorem_decl.strip().splitlines()[0]}")

        premises = self.retriever.retrieve_for_statement(theorem_decl)
        if premises:
            print(f"  → {len(premises)} lemmes Mathlib pertinents récupérés (LeanSearch + Loogle).")

        history: List[Dict[str, Any]] = []
        total_cost = 0.0

        def _run_loop(repl: LeanREPL) -> Tuple[bool, str]:
            nonlocal total_cost
            seen_premise_names = {p.name for p in premises}

            for iteration in range(1, self.config.max_attempts + 1):
                if total_cost >= self.config.budget_usd:
                    print(f"⚠️ Budget limite de ${self.config.budget_usd:.2f} atteint. Arrêt.")
                    break

                # 1. Escalade dynamique de modèle : tentatives 1-2 chat, tentatives 3+ reasoner
                if self.config.enable_escalation and iteration >= 3 and self.llm.deepseek_key:
                    active_model = "deepseek-reasoner"
                else:
                    active_model = self.config.model

                # 2. Retrieval dynamique sur but REPL et identifiants inconnus
                if history:
                    last_h = history[-1]
                    err = last_h.get("errors", "")
                    goals = last_h.get("goals", "")
                    if goals:
                        for gp in self.retriever.query_for_goal(goals, limit=3):
                            if gp.name not in seen_premise_names:
                                seen_premise_names.add(gp.name)
                                premises.append(gp)
                    if "unknown identifier" in err or "unknown constant" in err:
                        m = re.search(r"unknown (?:identifier|constant) [`']([a-zA-Z0-9_.']+)['`]", err)
                        if m:
                            for ip in self.retriever.query_for_unknown_identifier(m.group(1), limit=3):
                                if ip.name not in seen_premise_names:
                                    seen_premise_names.add(ip.name)
                                    premises.append(ip)

                current_temp = (
                    min(0.8, 0.1 + (iteration - 1) * 0.15)
                    if self.config.dynamic_temperature
                    else self.config.temperature
                )

                prompt = self.build_prompt(theorem_decl, premises, history, context_code=context_code)
                print(f"\n[Tentative {iteration}/{self.config.max_attempts}] Génération ({active_model}, temp={current_temp:.2f})...")

                # 3. Tir parallèle pass@k si configuré sur la 1ère tentative
                candidates_to_test = []
                if self.config.pass_k > 1 and iteration == 1:
                    print(f"  🚀 Tir parallèle pass@{self.config.pass_k} à températures variées...")
                    temps = [0.1, 0.4, 0.7][:self.config.pass_k]
                    while len(temps) < self.config.pass_k:
                        temps.append(0.5)

                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.pass_k) as executor:
                        futures = [
                            executor.submit(
                                self.llm.generate,
                                prompt,
                                theorem_decl,
                                iteration=iteration,
                                temperature=t,
                                model=active_model
                            )
                            for t in temps
                        ]
                        for f in futures:
                            raw_llm, p_tok, c_tok, cost = f.result()
                            total_cost += cost
                            candidates_to_test.append((raw_llm, p_tok, c_tok, cost))
                else:
                    raw_llm, p_tok, c_tok, cost = self.llm.generate(
                        prompt,
                        theorem_decl=theorem_decl,
                        iteration=iteration,
                        temperature=current_temp,
                        model=active_model
                    )
                    total_cost += cost
                    candidates_to_test.append((raw_llm, p_tok, c_tok, cost))

                # Évaluation des candidats
                best_failed_candidate = None
                min_errors = 999

                for raw_llm, p_tok, c_tok, cost in candidates_to_test:
                    candidate_code = self.sanitize_code(raw_llm, theorem_decl)
                    if context_code:
                        clean_candidate = "\n".join(
                            l for l in candidate_code.splitlines()
                            if not l.strip().startswith("import ")
                            and not l.strip().startswith("set_option ")
                            and not l.strip().startswith("open scoped ")
                        ).strip()
                        full_test_code = context_code.strip() + "\n\n" + clean_candidate
                    else:
                        full_test_code = candidate_code

                    # Test REPL avec timeout strict
                    print(f"  ⚡ Évaluation via LeanREPL (timeout={self.config.timeout_per_attempt_sec}s)...")
                    repl_resp = repl.check_code(full_test_code, timeout_sec=float(self.config.timeout_per_attempt_sec))

                    if repl_resp.is_success:
                        print(f"  ✨ REPL validé en {repl_resp.duration_ms:.1f}ms ! Envoi au Juge Final (LXC Prod)...")
                        prod_res = self.verifier.verify_file_content(full_test_code, temp_name=f"{problem_name}.lean")

                        self.db.record_attempt(
                            problem_name=problem_name,
                            iteration=iteration,
                            model=active_model,
                            prompt=prompt,
                            candidate_code=full_test_code,
                            success=prod_res.success,
                            compiler_errors=prod_res.error_message,
                            duration_ms=repl_resp.duration_ms,
                            prompt_tokens=p_tok,
                            completion_tokens=c_tok,
                            cost_usd=cost
                        )

                        if prod_res.success:
                            print(f"  🏆 PREUVE CERTIFIÉE SANS FAUTE en {iteration} itération(s) !")
                            return True, full_test_code
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
                        self.db.record_attempt(
                            problem_name=problem_name,
                            iteration=iteration,
                            model=active_model,
                            prompt=prompt,
                            candidate_code=full_test_code,
                            success=False,
                            compiler_errors=err_text,
                            unsolved_goals=goal_text,
                            duration_ms=repl_resp.duration_ms,
                            prompt_tokens=p_tok,
                            completion_tokens=c_tok,
                            cost_usd=cost
                        )
                        num_errs = len(repl_resp.error_texts) + len(repl_resp.goals)
                        if num_errs < min_errors:
                            min_errors = num_errs
                            best_failed_candidate = {
                                "code": candidate_code,
                                "errors": err_text,
                                "goals": goal_text
                            }

                if best_failed_candidate and not repl_resp.is_success:
                    history.append(best_failed_candidate)
            return False, ""

        if external_repl:
            success, code = _run_loop(external_repl)
        else:
            with LeanREPL() as repl:
                success, code = _run_loop(repl)

        if not success:
            print(f"❌ Échec : preuve non trouvée après {self.config.max_attempts} tentatives.")
        return success, code
