"""
Lean 4 REPL Client for AI-Maths-Researcher.
Provides sub-second interactive Lean 4 & Mathlib feedback over a persistent SSH connection.
Supports command execution, goal state extraction, and tactic verification.
"""

import json
import subprocess
import time
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class REPLMessage:
    severity: str
    data: str
    line: Optional[int] = None
    column: Optional[int] = None

@dataclass
class REPLResponse:
    raw: Dict[str, Any]
    env: Optional[int]
    messages: List[REPLMessage] = field(default_factory=list)
    sorries: List[Dict[str, Any]] = field(default_factory=list)
    proof_state: Optional[int] = None
    goals: List[str] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def has_errors(self) -> bool:
        return any(m.severity == "error" for m in self.messages)

    @property
    def error_texts(self) -> List[str]:
        return [m.data for m in self.messages if m.severity == "error"]

    @property
    def is_success(self) -> bool:
        return (not self.has_errors) and (len(self.sorries) == 0)

class LeanREPL:
    def __init__(
        self,
        host: str = "100.90.108.89",
        container_id: str = "200",
        project_dir: str = "/home/lean/projects/sun-formal",
        repl_bin: str = "/home/lean/repl/.lake/build/bin/repl",
    ):
        self.host = host
        self.container_id = container_id
        self.project_dir = project_dir
        self.repl_bin = repl_bin
        self.process: Optional[subprocess.Popen] = None
        self.current_env: Optional[int] = None

    def start(self):
        """Starts the persistent Lean REPL process over SSH."""
        if self.process is not None and self.process.poll() is None:
            return

        cmd = [
            "ssh",
            f"root@{self.host}",
            f"pct exec {self.container_id} -- su - lean -c 'source ~/.profile 2>/dev/null; cd {self.project_dir} && lake env {self.repl_bin}'"
        ]
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.current_env = None

    def close(self):
        """Terminates the REPL process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
            self.current_env = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def send_request(self, payload: Dict[str, Any]) -> REPLResponse:
        """Sends a raw JSON request to REPL and parses the response."""
        if not self.process or self.process.poll() is not None:
            self.start()

        t0 = time.perf_counter()
        req_str = json.dumps(payload) + "\n\n"
        self.process.stdin.write(req_str)
        self.process.stdin.flush()

        # Read JSON response until blank line
        lines = []
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            if line.strip() == "" and lines:
                break
            lines.append(line)

        t1 = time.perf_counter()
        duration_ms = (t1 - t0) * 1000

        raw_output = "".join(lines).strip()
        if not raw_output:
            return REPLResponse(raw={}, env=self.current_env, duration_ms=duration_ms)

        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            return REPLResponse(
                raw={"raw_error": raw_output},
                env=self.current_env,
                messages=[REPLMessage(severity="error", data=f"Invalid JSON from REPL: {raw_output}")],
                duration_ms=duration_ms
            )

        messages = []
        for m in data.get("messages", []):
            pos = m.get("pos", {})
            messages.append(
                REPLMessage(
                    severity=m.get("severity", "info"),
                    data=m.get("data", ""),
                    line=pos.get("line"),
                    column=pos.get("column")
                )
            )

        new_env = data.get("env", self.current_env)
        if new_env is not None:
            self.current_env = new_env

        # Extract goals if any
        goals = []
        for m in messages:
            if "unsolved goals" in m.data:
                goals.append(m.data)

        sorries = data.get("sorries", [])
        proof_state = data.get("proofState")

        return REPLResponse(
            raw=data,
            env=new_env,
            messages=messages,
            sorries=sorries,
            proof_state=proof_state,
            goals=goals,
            duration_ms=duration_ms
        )

    def check_code(self, code: str, reuse_env: bool = False) -> REPLResponse:
        """
        Executes a Lean code block.
        If reuse_env is True and an environment is active, reuses it to avoid re-importing.
        """
        payload: Dict[str, Any] = {"cmd": code}
        if reuse_env and self.current_env is not None:
            payload["env"] = self.current_env
        return self.send_request(payload)

    def run_tactic(self, tactic: str, proof_state: int) -> REPLResponse:
        """Executes a tactic on an existing proofState ID."""
        payload = {"tactic": tactic, "proofState": proof_state}
        return self.send_request(payload)
