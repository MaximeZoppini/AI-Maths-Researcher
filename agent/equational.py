"""
Equational Theories Prover for AI-Maths-Researcher.
Supports Phase 4 Target 2: Proving equational implications on Magmas
inspired by Terence Tao's 'Equational Theories' project.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any

from agent.repl_client import LeanREPL
from agent.prover import ProofSearchEngine, ProverConfig, LLMProvider
from agent.verifier import RemoteProdVerifier

MAGMA_HEADER = """
import Mathlib.Tactic

set_option linter.style.header false

class Magma (G : Type*) where
  op : G → G → G

local infixl:70 " ⬝ " => Magma.op
"""

@dataclass
class EquationalProblem:
    name: str
    hypothesis_eq: str
    conclusion_eq: str
    description: str

class EquationalProver:
    def __init__(self, config: Optional[ProverConfig] = None):
        self.config = config or ProverConfig()
        self.llm = LLMProvider(model=self.config.model)
        self.verifier = RemoteProdVerifier()

    def build_theorem_statement(self, prob: EquationalProblem) -> str:
        """Constructs the Lean 4 formal declaration for the magma implication."""
        return (
            f"theorem {prob.name} {{G : Type*}} [Magma G] "
            f"(h : {prob.hypothesis_eq}) : {prob.conclusion_eq}"
        )

    def prove_implication(self, prob: EquationalProblem, max_attempts: int = 4) -> Tuple[bool, str]:
        """
        Searches for a formal equational proof (chain of substitutions / calc).
        """
        decl = self.build_theorem_statement(prob)
        print(f"\n⚡ [Equational Theories] Recherche d'implication pour '{prob.name}'...")
        print(f"  Hypothèse  : {prob.hypothesis_eq}")
        print(f"  Conclusion : {prob.conclusion_eq}")

        history: List[str] = []

        with LeanREPL() as repl:
            for attempt in range(1, max_attempts + 1):
                prompt = f"""You are an elite formal mathematician working on Terence Tao's Equational Theories project in Lean 4.
Your objective is to prove an equational implication between two laws on a Magma (G, ⬝).

### Context:
```lean
class Magma (G : Type*) where
  op : G → G → G

local infixl:70 " ⬝ " => Magma.op
```

### Theorem to Prove:
```lean
{decl}
```

RULES:
1. Provide a complete, valid Lean 4 proof inside a ```lean ... ``` block.
2. Use substitution, `have`, `rw [h]`, `nth_rw`, or `calc` blocks.
3. No `sorry` allowed.
"""
                if history:
                    prompt += "\n### Previous Errors:\n" + "\n".join(history[-2:])

                raw_output, _, _, _ = self.llm.generate(prompt, prob.name, iteration=attempt, temperature=0.15 + attempt * 0.1)
                
                # Extract code
                import re
                matches = re.findall(r"```lean(.*?)```", raw_output, re.DOTALL)
                candidate_body = matches[-1].strip() if matches else raw_output.strip()

                if "theorem" not in candidate_body:
                    candidate_code = f"{decl} := by\n  {candidate_body}"
                else:
                    candidate_code = candidate_body

                full_lean = (MAGMA_HEADER + "\n\n" + candidate_code).strip()

                resp = repl.check_code(full_lean)
                if resp.is_success:
                    print(f"  ✨ REPL validé en {resp.duration_ms:.1f}ms ! Envoi au Juge Prod...")
                    prod_res = self.verifier.verify_file_content(full_lean, temp_name=f"{prob.name}.lean")
                    if prod_res.success:
                        print(f"  🏆 IMPLICATION ÉQUATIONNELLE CERTIFIÉE SANS FAUTE !")
                        return True, full_lean
                    else:
                        print(f"  ⚠️ Rejet Prod : {prod_res.error_message}")
                        history.append(prod_res.error_message or "Prod rejected")
                else:
                    err_summary = "\n".join(resp.error_texts)
                    print(f"  ❌ Échec REPL ({resp.duration_ms:.1f}ms) : {err_summary[:100]}...")
                    history.append(err_summary)

        return False, ""

if __name__ == "__main__":
    prover = EquationalProver()
    # Test classic equational identity: (x ⬝ y = x) implies (x ⬝ (y ⬝ z) = x)
    test_prob = EquationalProblem(
        name="eq_proj_left_trans",
        hypothesis_eq="∀ x y : G, x ⬝ y = x",
        conclusion_eq="∀ x y z : G, x ⬝ (y ⬝ z) = x",
        description="Left projection implies generalized left projection"
    )
    prover.prove_implication(test_prob)
