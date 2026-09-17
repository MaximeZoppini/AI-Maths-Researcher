"""
Blueprint Planner & Lemma Decomposition Engine for AI-Maths-Researcher.
Implements Phase 2 of VISION.md.txt:
1. Generates Natural Language proof strategy.
2. Constructs Lean 4 skeleton with intermediate lemmas (using `sorry`).
3. Validates skeleton in REPL (fast syntax & reduction check).
4. Solves each sub-lemma iteratively via ProofSearchEngine.
5. Assembles complete, sorry-free file and verifies via Level 2 #print axioms audit.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

from agent.repl_client import LeanREPL
from agent.verifier import RemoteProdVerifier, VerificationResult
from agent.prover import ProofSearchEngine, ProverConfig, LLMProvider
from agent.retrieval import PremiseRetriever
from agent.db import AttemptsDB

@dataclass
class LemmaSkeleton:
    name: str
    declaration: str
    is_solved: bool = False
    proof_code: str = ""

@dataclass
class Blueprint:
    problem_name: str
    theorem_decl: str
    nl_plan: str
    lemmas: List[LemmaSkeleton] = field(default_factory=list)
    main_theorem_code: str = ""
    raw_skeleton: str = ""

class BlueprintPlanner:
    def __init__(self, config: Optional[ProverConfig] = None):
        self.config = config or ProverConfig()
        self.llm = LLMProvider(model=self.config.model)
        self.retriever = PremiseRetriever()
        self.verifier = RemoteProdVerifier()
        self.db = AttemptsDB()
        self.prover = ProofSearchEngine(config=self.config)

    def create_blueprint(self, theorem_decl: str, problem_name: str) -> Optional[Blueprint]:
        """
        Prompts LLM to produce an NL plan + a Lean 4 skeleton with intermediate lemmas.
        """
        premises = self.retriever.retrieve_for_statement(theorem_decl)
        retrieval_block = self.retriever.format_prompt_block(premises) if premises else ""

        prompt = f"""You are a master formal mathematician and blueprint architect in Lean 4 and Mathlib.
The goal is to prove the following target theorem by decomposing it into 1 to 3 logical intermediate steps (lemmas).

### Target Theorem:
```lean
{theorem_decl}
```

{retrieval_block}

INSTRUCTIONS:
1. Write a short Natural Language Plan explaining the mathematical strategy (e.g., modular arithmetic, case analysis, key inequalities, algebraic substitutions).
2. Provide a Lean 4 code skeleton containing:
   - Necessary imports at top (`import Mathlib.Tactic`, `import Mathlib.Data.Real.Basic`, etc.)
   - 1 to 3 helper lemmas (`lemma {problem_name}_step1 ... := by sorry`)
   - The target theorem whose proof uses the helper lemmas (`theorem {problem_name} ... := by ...`)
3. The skeleton MUST be syntactically valid Lean 4 so it can compile with `sorry`.

Format your answer as:
### Natural Language Plan
<Your explanation>

### Lean 4 Skeleton
```lean
<Lean 4 code>
```
"""
        raw_output, p_tok, c_tok, cost = self.llm.generate(
            prompt=prompt,
            theorem_decl=theorem_decl,
            iteration=1,
            temperature=0.2
        )

        # Extract NL Plan
        nl_plan = ""
        nl_match = re.search(r"### Natural Language Plan\s*(.*?)(?=### Lean 4 Skeleton|```lean|$)", raw_output, re.DOTALL)
        if nl_match:
            nl_plan = nl_match.group(1).strip()

        # Extract Lean Skeleton
        code_matches = re.findall(r"```lean(.*?)```", raw_output, re.DOTALL)
        skeleton_code = code_matches[-1].strip() if code_matches else ""
        if not skeleton_code:
            return None

        # Normalize imports
        skeleton_code = re.sub(
            r"^\s*import\s+Mathlib\s*$",
            "import Mathlib.Tactic\nimport Mathlib.Data.Real.Basic\nimport Mathlib.Algebra.Ring.Parity",
            skeleton_code,
            flags=re.MULTILINE
        )
        if not skeleton_code.startswith("import"):
            skeleton_code = "import Mathlib.Tactic\nimport Mathlib.Data.Real.Basic\nimport Mathlib.Algebra.Ring.Parity\n\n" + skeleton_code

        # Parse lemmas and main theorem
        lemmas = []
        decl_pattern = r"(lemma\s+([a-zA-Z0-9_']+)\s+([\s\S]*?):=(?:[\s\S]*?)(?=(?:\nlemma\s+|\ntheorem\s+|\Z)))"
        for match, lemma_name, lemma_body in re.findall(decl_pattern, skeleton_code):
            decl_stmt = f"lemma {lemma_name} {lemma_body}".strip()
            lemmas.append(LemmaSkeleton(name=lemma_name, declaration=decl_stmt))

        # Main theorem code
        main_match = re.search(r"(theorem\s+[\s\S]*)", skeleton_code)
        main_theorem_code = main_match.group(1).strip() if main_match else ""

        return Blueprint(
            problem_name=problem_name,
            theorem_decl=theorem_decl,
            nl_plan=nl_plan,
            lemmas=lemmas,
            main_theorem_code=main_theorem_code,
            raw_skeleton=skeleton_code
        )

    def verify_skeleton(self, skeleton_code: str, repl: LeanREPL) -> Tuple[bool, str]:
        """Validates that the skeleton compiles in REPL (allowing sorry)."""
        resp = repl.check_code(skeleton_code)
        if resp.is_valid_syntax:
            return True, ""
        return False, "\n".join(resp.error_texts)

    def prove_with_blueprint(self, theorem_decl: str, problem_name: str = "Candidate") -> Tuple[bool, str]:
        """
        Executes the full Blueprint workflow:
        1. Create blueprint.
        2. Validate skeleton in REPL.
        3. Solve each lemma sequentially via ProofSearchEngine.
        4. Solve the main theorem using the proven lemmas.
        5. Verify final code without sorry on prod LXC.
        """
        print(f"\n🗺️  [Blueprint] Élaboration du plan pour '{problem_name}'...")
        blueprint = self.create_blueprint(theorem_decl, problem_name)
        if not blueprint:
            print("  ❌ Échec de génération du blueprint.")
            return False, ""

        print(f"  📝 Plan en langage naturel :\n{blueprint.nl_plan[:250]}...\n")
        print(f"  🧩 {len(blueprint.lemmas)} lemme(s) intermédiaire(s) identifié(s) :")
        for lem in blueprint.lemmas:
            print(f"    - {lem.name} : {lem.declaration[:70]}...")

        with LeanREPL() as repl:
            # Step 1: Verify skeleton compiles in REPL
            print("  ⚡ Vérification du squelette en mémoire REPL...")
            skel_ok, skel_err = self.verify_skeleton(blueprint.raw_skeleton, repl)
            if not skel_ok:
                print(f"  ⚠️ Le squelette a échoué en REPL : {skel_err[:150]}...")
            else:
                print("  ✨ Squelette validé ! La réduction mathématique est cohérente.")

            # Step 2: Sequentially prove each lemma
            solved_lemmas_code = []
            standard_headers = (
                "import Mathlib.Tactic\n"
                "import Mathlib.Data.Real.Basic\n"
                "import Mathlib.Algebra.Ring.Parity\n"
                "import Mathlib.Data.Nat.Factorial.Basic\n\n"
                "open scoped Nat\n"
                "open scoped Real\n\n"
                "set_option linter.style.header false\n\n"
            )

            for idx, lemma in enumerate(blueprint.lemmas, 1):
                print(f"\n  🔍 [Lemme {idx}/{len(blueprint.lemmas)}] Recherche de preuve pour '{lemma.name}'...")
                current_context = standard_headers + "\n\n".join(solved_lemmas_code)
                
                l_success, l_code = self.prover.prove_theorem(
                    theorem_decl=lemma.declaration,
                    problem_name=f"{problem_name}_{lemma.name}",
                    context_code=current_context,
                    external_repl=repl
                )

                if l_success:
                    print(f"    ✅ Lemme '{lemma.name}' PROUVÉ ET VALIDÉ !")
                    lemma.is_solved = True
                    lemma.proof_code = l_code
                    clean_lemma = l_code
                    for imp in ["import Mathlib", "set_option linter"]:
                        clean_lemma = "\n".join([line for line in clean_lemma.splitlines() if not line.strip().startswith(imp)])
                    solved_lemmas_code.append(clean_lemma.strip())
                else:
                    print(f"    ❌ Échec de résolution du lemme '{lemma.name}'.")
                    return False, ""

            # Step 3: Now prove or assemble the main theorem
            print(f"\n  🎯 [Théorème Principal] Assemblage et résolution finale de '{problem_name}'...")
            full_context = standard_headers + "\n\n".join(solved_lemmas_code)
            
            if "sorry" not in blueprint.main_theorem_code and blueprint.main_theorem_code:
                candidate_full = full_context + "\n\n" + blueprint.main_theorem_code
                test_resp = repl.check_code(candidate_full)
                if test_resp.is_success:
                    print("  ✨ Preuve d'assemblage validée en REPL !")
                    prod_res = self.verifier.verify_file_content(candidate_full, temp_name=f"{problem_name}.lean")
                    if prod_res.success:
                        print(f"  🏆 PREUVE GLOBALE CERTIFIÉE PAR LE JUGE FINAL (#print axioms) !")
                        return True, candidate_full

            success, final_code = self.prover.prove_theorem(
                theorem_decl=theorem_decl,
                problem_name=problem_name,
                context_code=full_context,
                external_repl=repl
            )

            if success:
                print(f"  🏆 PROBLÈME RÉSOLU VIA BLUEPRINT & DÉCOMPOSITION EN LEMMES !")
                return True, final_code
            else:
                print(f"  ❌ Échec de la preuve finale du théorème principal.")
                return False, ""
