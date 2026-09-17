import subprocess
import os
import re
from dataclasses import dataclass
from typing import Optional, List, Tuple

@dataclass
class VerificationResult:
    success: bool
    has_sorry_or_axiom: bool
    error_message: Optional[str]
    stdout: str
    stderr: str
    unsolved_goals: List[str]

class RemoteProdVerifier:
    def __init__(self, host: str = "100.90.108.89", container_id: str = "200"):
        self.host = host
        self.container_id = container_id
        self.project_dir = "/home/lean/projects/sun-formal"

    def verify_file_content(self, lean_code: str, temp_name: str = "CandidateProof.lean") -> VerificationResult:
        """
        Sends Lean code to the remote LXC container, compiles with Mathlib, and returns detailed compiler diagnostic.
        """
        # Escape single quotes in lean code for bash
        escaped_code = lean_code.replace("'", "'\\''")
        remote_cmd = (
            f"source ~/.profile 2>/dev/null; cd {self.project_dir} && "
            f"cat << 'EOF' > problems/{temp_name}\n{lean_code}\nEOF\n"
            f"lake env lean problems/{temp_name}"
        )
        
        ssh_cmd = [
            "ssh",
            f"root@{self.host}",
            f"pct exec {self.container_id} -- su - lean -c '{remote_cmd}'"
        ]
        
        proc = subprocess.run(ssh_cmd, capture_output=True, text=True)
        return self._parse_output(proc.stdout, proc.stderr, proc.returncode, lean_code)

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

    def _parse_output(self, stdout: str, stderr: str, return_code: int, code: str) -> VerificationResult:
        combined = stdout + "\n" + stderr
        has_sorry = bool(re.search(r"\b(sorry|axiom)\b", code))
        
        # Check for unsolved goals
        unsolved = re.findall(r"unsolved goals.*?(?=\n\n|\Z)", combined, re.DOTALL)
        
        # Check if lean compiler exited cleanly with 0 and no error reported
        success = (return_code == 0) and ("error:" not in combined) and (not has_sorry)
        
        error_msg = None
        if not success:
            errors = [line for line in combined.splitlines() if "error:" in line or "unsolved goals" in line]
            error_msg = "\n".join(errors) if errors else combined.strip()

        return VerificationResult(
            success=success,
            has_sorry_or_axiom=has_sorry,
            error_message=error_msg,
            stdout=stdout,
            stderr=stderr,
            unsolved_goals=unsolved
        )
