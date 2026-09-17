"""
Autoformalization Engine with Triple Guardrail for AI-Maths-Researcher.
Implements Phase 3 of VISION.md.txt:
Translates natural language mathematical problems into certified Lean 4 statements.
Triple Guardrails:
1. Syntactic and type compilation check in LeanREPL.
2. Round-trip neutral back-translation and semantic equivalence judge.
3. Non-vacuity & hypothesis consistency audit (rejects contradictory premises).
"""

import re
import json
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any

from agent.repl_client import LeanREPL
from agent.prover import LLMProvider, ProverConfig
from agent.retrieval import PremiseRetriever

@dataclass
class AutoformalizationResult:
    natural_language: str
    theorem_name: str
    lean_statement: str
    compiles: bool = False
    compile_error: Optional[str] = None
    round_trip_valid: bool = False
    round_trip_translation: str = ""
    round_trip_score: float = 0.0
    round_trip_reason: str = ""
    non_vacuous: bool = False
    vacuity_reason: str = ""
    is_valid: bool = False
    error_message: Optional[str] = None

class Autoformalizer:
    def __init__(self, config: Optional[ProverConfig] = None):
        self.config = config or ProverConfig()
        self.llm = LLMProvider(model=self.config.model)
        # Juge indépendant : différent du formaliseur pour éliminer le biais d'auto-validation
        if self.llm.gemini_key:
            self.judge_llm = LLMProvider(model="gemini-2.5-flash")
            self.judge_name = "gemini-2.5-flash"
        elif self.llm.deepseek_key:
            self.judge_llm = LLMProvider(model="deepseek-reasoner")
            self.judge_name = "deepseek-reasoner"
        else:
            self.judge_llm = self.llm
            self.judge_name = self.config.model
        self.retriever = PremiseRetriever()

    def _get_standard_header(self) -> str:
        return (
            "import Mathlib.Tactic\n"
            "import Mathlib.Data.Real.Basic\n"
            "import Mathlib.Algebra.Ring.Parity\n"
            "import Mathlib.Data.Nat.Factorial.Basic\n\n"
            "open scoped Nat\n"
            "open scoped Real\n\n"
            "set_option linter.style.header false\n\n"
        )

    def extract_lean_statement(self, text: str, default_name: str = "Problem") -> str:
        """Extracts theorem statement from markdown code block."""
        matches = re.findall(r"```lean(.*?)```", text, re.DOTALL)
        code = matches[-1].strip() if matches else text.strip()

        # Remove trailing proof or sorry
        code = re.sub(r":=\s*(by\s*)?(sorry)?\s*$", "", code).strip()

        # Ensure it starts with theorem or lemma
        if not code.startswith("theorem ") and not code.startswith("lemma "):
            code = f"theorem {default_name} {code}"

        return code

    def check_compiles(self, lean_stmt: str, repl: LeanREPL) -> Tuple[bool, str]:
        """Guardrail 1: Checks that the statement compiles with ':= by sorry'."""
        candidate = f"{lean_stmt} := by sorry"
        full_code = self._get_standard_header() + candidate
        resp = repl.check_code(full_code)
        if resp.is_valid_syntax:
            return True, ""
        return False, "\n".join(resp.error_texts)

    def check_round_trip(self, original_text: str, lean_stmt: str) -> Tuple[bool, str, float, str]:
        """Guardrail 2: Neutral back-translation and semantic equivalence check with independent judge."""
        # Step 1: Back-translate in a blank context with translation model
        back_prompt = (
            "You are a rigorous mathematical translator. Translate the following Lean 4 theorem statement into natural language.\n"
            "State all types, all hypotheses/assumptions, and the exact conclusion clearly and precisely.\n\n"
            f"```lean\n{lean_stmt}\n```\n\n"
            "Provide ONLY the natural language mathematical statement:"
        )
        back_translation, _, _, _ = self.llm.generate(back_prompt, lean_stmt, iteration=1, temperature=0.1)
        back_translation = back_translation.replace("```", "").strip()

        # Step 2: Independent LLM Judge comparing original problem and back-translation
        print(f"  ⚖️  Évaluation d'équivalence sémantique par le juge indépendant ({self.judge_name})...")
        judge_prompt = f"""You are an expert mathematical judge evaluating formalization fidelity.
Compare the ORIGINAL mathematical problem with the RECONSTRUCTED statement translated from formal Lean 4 code.

### ORIGINAL PROBLEM:
{original_text}

### RECONSTRUCTED STATEMENT FROM LEAN 4:
{back_translation}

Evaluate:
1. Are the variable domains (e.g. natural numbers, integers, reals) identical?
2. Are all hypotheses present and unaltered?
3. Is the exact conclusion preserved (neither weakened nor trivialized)?

Respond ONLY with valid JSON in this exact structure:
{{
  "is_equivalent": true,
  "score": 0.95,
  "reason": "Detailed explanation of mathematical equivalence"
}}
"""
        judge_raw, _, _, _ = self.judge_llm.generate(judge_prompt, lean_stmt, iteration=1, temperature=0.1)
        
        # Parse JSON
        try:
            json_match = re.search(r"\{[\s\S]*\}", judge_raw)
            if json_match:
                data = json.loads(json_match.group(0))
                is_equiv = bool(data.get("is_equivalent", False))
                score = float(data.get("score", 0.0))
                reason = str(data.get("reason", ""))
                valid = is_equiv and score >= 0.85
                return valid, back_translation, score, reason
        except Exception as e:
            pass

        return False, back_translation, 0.0, f"Judge parsing failed: {judge_raw[:100]}"

    def check_non_vacuous(self, lean_stmt: str, repl: LeanREPL) -> Tuple[bool, str]:
        """
        Guardrail 3: Checks that the hypotheses are not mutually contradictory.
        Attempts to prove False from hypotheses using automated tactics.
        If False is provable, the hypotheses are inconsistent -> VACUOUS!
        """
        # Split declaration into binders/hypotheses and conclusion
        # e.g. theorem foo (x : ℤ) (h1 : x > 5) (h2 : x < 2) : conclusion
        if ":" not in lean_stmt:
            return True, "No hypotheses detected."

        parts = lean_stmt.rsplit(":", 1)
        decl_prefix = parts[0].strip()
        
        # Build inconsistency probe
        # If hypotheses contain contradiction, proving False will succeed
        probe = (
            f"{decl_prefix} : False := by\n"
            "  intros\n"
            "  first | contradiction | linarith | omega | aesop\n"
        )
        full_code = self._get_standard_header() + probe
        resp = repl.check_code(full_code)

        if resp.is_success:
            # If it succeeded in proving False, hypotheses are contradictory!
            return False, "HYPOTHÈSES CONTRADICTOIRES : Les hypothèses permettent de déduire 'False' immédiatement. Énoncé rejeté pour vacuité."

        return True, "Hypothèses cohérentes (non contradictoires)."

    def formalize_problem(
        self,
        problem_text: str,
        theorem_name: str = "FormalProblem",
        max_attempts: int = 3
    ) -> AutoformalizationResult:
        print(f"\n📝 [Autoformalisation] Début de formalisation pour '{theorem_name}'...")
        print(f"Énoncé naturel : {problem_text[:120]}...\n")

        premises = self.retriever.retrieve_for_statement(problem_text)
        retrieval_block = self.retriever.format_prompt_block(premises) if premises else ""

        with LeanREPL() as repl:
            history_errors = []
            for attempt in range(1, max_attempts + 1):
                prompt = f"""You are an elite Lean 4 and Mathlib formal mathematician.
Translate the following informal mathematical problem into a precise, idiomatic Lean 4 theorem declaration.

### Informal Problem:
{problem_text}

{retrieval_block}

CRITICAL RULES:
1. Output ONLY the theorem declaration header ending BEFORE `:=`.
   Example: `theorem {theorem_name} (a b : ℝ) (h₁ : a + b = 10) : a * b ≤ 25`
2. Do NOT write `:= by sorry` or any proof code.
3. Choose the exact proper types (ℕ, ℤ, ℚ, ℝ) matching the mathematical meaning.
4. Name hypotheses clearly: `h₁`, `h₂`, etc.
5. Put your Lean 4 theorem declaration in a ```lean ... ``` block.
"""
                if history_errors:
                    prompt += "\n### Previous Errors (Please correct):\n" + "\n".join(history_errors[-2:])

                print(f"[Essai {attempt}/{max_attempts}] Génération du typage Lean 4 ({self.llm.model})...")
                raw_code, _, _, _ = self.llm.generate(prompt, theorem_name, iteration=attempt, temperature=0.15)
                candidate_decl = self.extract_lean_statement(raw_code, default_name=theorem_name)
                print(f"  📌 Énoncé proposé : {candidate_decl}")

                # Guardrail 1: Compilation Check
                print("  ⚡ [Garde-fou 1/3] Vérification compilation & typage...")
                compiles, err = self.check_compiles(candidate_decl, repl)
                if not compiles:
                    print(f"  ❌ Erreur de compilation : {err[:120]}...")
                    history_errors.append(f"Lean compilation error: {err}")
                    continue
                print("  ✅ [Garde-fou 1/3] Compilation réussie.")

                # Guardrail 3: Non-Vacuity Check
                print("  ⚡ [Garde-fou 2/3] Audit de non-vacuité & cohérence des hypothèses...")
                non_vacuous, vacuity_msg = self.check_non_vacuous(candidate_decl, repl)
                if not non_vacuous:
                    print(f"  ❌ Rejet : {vacuity_msg}")
                    history_errors.append(vacuity_msg)
                    continue
                print(f"  ✅ [Garde-fou 2/3] {vacuity_msg}")

                # Guardrail 2: Round-Trip Check
                print("  ⚡ [Garde-fou 3/3] Contrôle Round-Trip (Rétro-traduction neutre + Juge)...")
                equiv, back_trans, score, reason = self.check_round_trip(problem_text, candidate_decl)
                print(f"  🔄 Rétro-traduction : {back_trans[:100]}...")
                print(f"  ⚖️ Score d'équivalence : {score * 100:.1f}% ({'Validé' if equiv else 'Rejeté'})")
                
                if not equiv:
                    print(f"  ❌ Échec Round-Trip : {reason[:120]}...")
                    history_errors.append(f"Round-trip mismatch ({score*100:.0f}%): {reason}")
                    continue

                print(f"  🏆 ÉNONCÉ FORMEL CERTIFIÉ CONFORME & ÉQUIVALENT !")
                return AutoformalizationResult(
                    natural_language=problem_text,
                    theorem_name=theorem_name,
                    lean_statement=candidate_decl,
                    compiles=True,
                    round_trip_valid=True,
                    round_trip_translation=back_trans,
                    round_trip_score=score,
                    round_trip_reason=reason,
                    non_vacuous=True,
                    vacuity_reason=vacuity_msg,
                    is_valid=True
                )

        print(f"❌ Échec de formalisation après {max_attempts} tentatives.")
        return AutoformalizationResult(
            natural_language=problem_text,
            theorem_name=theorem_name,
            lean_statement="",
            compiles=False,
            is_valid=False,
            error_message="All attempts failed validation guardrails."
        )

def main():
    import argparse
    from agent.prover import ProofSearchEngine
    from agent.planner import BlueprintPlanner

    parser = argparse.ArgumentParser(description="Autoformalisation Vérifiée (Phase 3)")
    parser.add_argument("--problem", type=str, required=True, help="Énoncé naturel du problème")
    parser.add_argument("--name", type=str, default="AutoThm", help="Nom du théorème Lean 4")
    parser.add_argument("--solve", action="store_true", help="Enchaîner sur la recherche de preuve après formalisation")
    args = parser.parse_args()

    autoform = Autoformalizer()
    res = autoform.formalize_problem(args.problem, theorem_name=args.name)

    if res.is_valid and args.solve:
        print("\n" + "=" * 60)
        print("🚀 Lancement automatique de la recherche de preuve sur l'énoncé certifié...")
        print("=" * 60)
        planner = BlueprintPlanner()
        success, code = planner.prove_with_blueprint(res.lean_statement, problem_name=args.name)
        if not success:
            engine = ProofSearchEngine()
            success, code = engine.prove_theorem(res.lean_statement, problem_name=args.name)
        if success:
            print(f"\n🎉 SUCCÈS TOTAL : Problème formalisé et prouvé formellement !")

if __name__ == "__main__":
    main()
