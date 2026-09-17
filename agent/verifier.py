import subprocess
import os
import re
from dataclasses import dataclass, field
from typing import Optional, List, Set, Tuple

ALLOWED_AXIOMS: Set[str] = {"propext", "Classical.choice", "Quot.sound"}

@dataclass
class VerificationResult:
    success: bool
    axioms_valid: bool
    theorems_audited: List[str]
    used_axioms: Set[str]
    unauthorized_axioms: Set[str]
    has_sorry_axiom: bool
    error_message: Optional[str]
    stdout: str
    stderr: str
    unsolved_goals: List[str] = field(default_factory=list)

class RemoteProdVerifier:
    def __init__(self, host: str = "100.90.108.89", container_id: str = "200"):
        self.host = host
        self.container_id = container_id
        self.project_dir = "/home/lean/projects/sun-formal"

    def verify_file_content(self, lean_code: str, temp_name: str = "CandidateProof.lean") -> VerificationResult:
        """
        Sends Lean code via stdin over SSH, runs Lean compiler + #print axioms on the LXC container,
        and returns complete mathematical and syntactic verification.
        """
        # Find all theorems and lemmas declared in the file (ignoring comments)
        clean_code = re.sub(r"/-[\s\S]*?-/", "", lean_code)
        clean_code = re.sub(r"--.*$", "", clean_code, flags=re.MULTILINE)
        theorems = re.findall(r"\b(?:theorem|lemma)\s+([a-zA-Z0-9_']+)", clean_code)
        
        # Prepare code with #print axioms appended for each theorem
        audit_code = lean_code
        if theorems:
            audit_code += "\n\n-- Automated Formal Axiom Audit\n"
            for thm in theorems:
                audit_code += f"#print axioms {thm}\n"

        # Pass code cleanly via stdin pipe over SSH
        remote_cmd = (
            f"source ~/.profile 2>/dev/null; cd {self.project_dir} && "
            f"cat > problems/{temp_name} && "
            f"lake env lean problems/{temp_name}"
        )
        
        ssh_cmd = [
            "ssh",
            f"root@{self.host}",
            f"pct exec {self.container_id} -- su - lean -c \"{remote_cmd}\""
        ]
        
        proc = subprocess.run(
            ssh_cmd,
            input=audit_code,
            capture_output=True,
            text=True
        )
        
        return self._parse_output(proc.stdout, proc.stderr, proc.returncode, lean_code, theorems)

    def run_prod_check(self) -> Tuple[bool, str]:
        """
        Runs the full ./scripts/check.sh on the prod container.
        """
        ssh_cmd = [
            "ssh",
            f"root@{self.host}",
            f"pct exec {self.container_id} -- su - lean -c 'source ~/.profile && cd {self.project_dir} && ./scripts/check.sh'"
        ]
        proc = subprocess.run(ssh_cmd, capture_output=True, text=True)
        return (proc.returncode == 0, proc.stdout + proc.stderr)

    def _parse_output(
        self, stdout: str, stderr: str, return_code: int, code: str, theorems: List[str]
    ) -> VerificationResult:
        combined = stdout + "\n" + stderr
        
        # Parse axioms: e.g. 'even_of_even_sq' depends on axioms: [propext, Classical.choice, Quot.sound]
        used_axioms = set()
        axiom_matches = re.findall(r"depends on axioms:\s*\[(.*?)\]", combined)
        for ax_list in axiom_matches:
            for ax in ax_list.split(","):
                ax_clean = ax.strip()
                if ax_clean:
                    used_axioms.add(ax_clean)
        
        has_sorry_axiom = "sorryAx" in used_axioms or bool(re.search(r"\b(sorry)\b", code))
        unauthorized_axioms = used_axioms - ALLOWED_AXIOMS
        axioms_valid = (not has_sorry_axiom) and (len(unauthorized_axioms) == 0)

        # Parse unsolved goals
        unsolved = re.findall(r"unsolved goals.*?(?=\n\n|\Z)", combined, re.DOTALL)
        
        # Compilation status
        has_compiler_error = (return_code != 0) or ("error:" in combined)
        success = (not has_compiler_error) and axioms_valid

        error_msg = None
        if not success:
            errors = [line for line in combined.splitlines() if "error:" in line or "unsolved goals" in line]
            if has_sorry_axiom:
                errors.append("Validation Error: Proof depends on 'sorry' / 'sorryAx'.")
            if unauthorized_axioms:
                errors.append(f"Axiom Audit Error: Unauthorized axioms detected: {unauthorized_axioms}")
            error_msg = "\n".join(errors) if errors else combined.strip()

        return VerificationResult(
            success=success,
            axioms_valid=axioms_valid,
            theorems_audited=theorems,
            used_axioms=used_axioms,
            unauthorized_axioms=unauthorized_axioms,
            has_sorry_axiom=has_sorry_axiom,
            error_message=error_msg,
            stdout=stdout,
            stderr=stderr,
            unsolved_goals=unsolved
        )
