"""
Lean 4 REPL Client for AI-Maths-Researcher.
Provides sub-second interactive Lean 4 & Mathlib feedback over a persistent SSH connection.
Maintains a warm base Mathlib environment for zero-overhead candidate evaluation.
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

    @property
    def is_valid_syntax(self) -> bool:
        """Returns True if the code compiled without errors (sorries are permitted)."""
        return not self.has_errors

import queue
import threading

class LeanREPL:
    def __init__(
        self,
        host: str = "100.90.108.89",
        container_id: str = "200",
        project_dir: str = "/home/lean/projects/sun-formal",
        repl_bin: str = "/home/lean/repl/.lake/build/bin/repl",
        full_mathlib: bool = False,
        default_timeout_sec: float = 25.0
    ):
        self.host = host
        self.container_id = container_id
        self.project_dir = project_dir
        self.repl_bin = repl_bin
        self.full_mathlib = full_mathlib
        self.default_timeout_sec = default_timeout_sec
        self.process: Optional[subprocess.Popen] = None
        self.base_env: Optional[int] = None
        self.line_queue: Optional[queue.Queue] = None
        self._is_warmup: bool = False

    def start(self):
        """Starts the persistent Lean REPL process over SSH and preloads Mathlib."""
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
        self.base_env = None

        # Start dedicated background thread to read stdout lines into queue
        self.line_queue = queue.Queue()
        def _stdout_worker():
            try:
                for line in iter(self.process.stdout.readline, ""):
                    if self.line_queue is not None:
                        self.line_queue.put(line)
            except Exception:
                pass
        reader_thread = threading.Thread(target=_stdout_worker, daemon=True)
        reader_thread.start()

        # Preload Mathlib modules into base_env
        self._is_warmup = True
        try:
            if self.full_mathlib:
                print("⏳ Initialisation REPL avec Mathlib complet (peut prendre ~2 min)...")
                warmup_cmd = (
                    "import Mathlib\n"
                    "open scoped Nat\n"
                    "open scoped Real\n"
                    "set_option linter.style.header false\n\n"
                    "theorem __base_init__ : True := trivial"
                )
                warmup_timeout = 180.0
            else:
                # Fast comprehensive Mathlib suite (takes ~4s)
                warmup_cmd = (
                    "import Mathlib.Tactic\n"
                    "import Mathlib.Algebra.Ring.Parity\n"
                    "import Mathlib.Data.Real.Basic\n"
                    "import Mathlib.Data.Nat.Factorial.Basic\n"
                    "open scoped Nat\n"
                    "open scoped Real\n"
                    "set_option linter.style.header false\n\n"
                    "theorem __base_init__ : True := trivial"
                )
                warmup_timeout = 30.0

            resp = self.send_request({"cmd": warmup_cmd}, timeout_sec=warmup_timeout)
            if resp.env is not None:
                self.base_env = resp.env
        finally:
            self._is_warmup = False

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
            self.base_env = None
            self.line_queue = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def send_request(self, payload: Dict[str, Any], timeout_sec: Optional[float] = None) -> REPLResponse:
        """Sends a raw JSON request to REPL and parses the response with strict timeout and auto-recovery."""
        if not self.process or self.process.poll() is not None:
            self.start()

        effective_timeout = timeout_sec if timeout_sec is not None else self.default_timeout_sec
        t0 = time.perf_counter()
        req_str = json.dumps(payload) + "\n\n"
        try:
            self.process.stdin.write(req_str)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            print("⚠️ Pipe REPL brisé. Redémarrage...")
            self.close()
            self.start()
            self.process.stdin.write(req_str)
            self.process.stdin.flush()

        # Read JSON response with timeout from thread-safe queue
        lines = []
        deadline = time.perf_counter() + effective_timeout
        timed_out = False

        while True:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                timed_out = True
                break

            try:
                line = self.line_queue.get(timeout=max(0.01, remaining))
            except (queue.Empty, AttributeError):
                timed_out = True
                break

            if not line:
                break
            if line.strip() == "" and lines:
                break
            lines.append(line)

        if timed_out:
            print(f"\n⏱️ REPL Timeout dépassé ({effective_timeout:.1f}s). Redémarrage automatique...")
            self.close()
            self.start()
            return REPLResponse(
                raw={"error": "timeout"},
                env=self.base_env,
                messages=[
                    REPLMessage(
                        severity="error",
                        data=f"Tactic evaluation timed out (> {effective_timeout:.1f}s). The tactic likely diverged. Please try an alternative approach or decompose using intermediate lemmas."
                    )
                ],
                duration_ms=effective_timeout * 1000
            )

        t1 = time.perf_counter()
        duration_ms = (t1 - t0) * 1000

        raw_output = "".join(lines).strip()
        if not raw_output:
            return REPLResponse(raw={}, env=self.base_env, duration_ms=duration_ms)

        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            return REPLResponse(
                raw={"raw_error": raw_output},
                env=self.base_env,
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

        new_env = data.get("env")

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

    def check_code(self, code: str, timeout_sec: Optional[float] = None) -> REPLResponse:
        """
        Executes candidate Lean code in the preloaded Mathlib base environment.
        Strips redundant import lines since Mathlib is already in memory.
        """
        # Strip import statements for REPL execution against base_env
        cleaned_lines = [l for l in code.splitlines() if not l.strip().startswith("import ")]
        cleaned_code = "\n".join(cleaned_lines).strip()

        payload: Dict[str, Any] = {"cmd": cleaned_code}
        if self.base_env is not None:
            payload["env"] = self.base_env

        return self.send_request(payload, timeout_sec=timeout_sec)

import contextlib

class REPLPool:
    """Pool of persistent LeanREPL instances under lock for multi-threaded proof search."""
    def __init__(
        self,
        size: int = 2,
        host: str = "100.90.108.89",
        container_id: str = "200",
        full_mathlib: bool = False
    ):
        self.size = size
        self.host = host
        self.container_id = container_id
        self.full_mathlib = full_mathlib
        self._pool: queue.Queue = queue.Queue(maxsize=size)
        self._repls: List[LeanREPL] = []
        self._lock = threading.Lock()
        self._initialized = False

    def start(self):
        with self._lock:
            if self._initialized:
                return
            print(f"🚀 Initialisation du pool REPL ({self.size} workers persistent SSH)...")
            for i in range(self.size):
                print(f"  → Démarrage REPL #{i+1}...")
                repl = LeanREPL(
                    host=self.host,
                    container_id=self.container_id,
                    full_mathlib=self.full_mathlib
                )
                repl.start()
                self._repls.append(repl)
                self._pool.put(repl)
            self._initialized = True
            print(f"✅ Pool REPL opérationnel ({self.size} instances).")

    @contextlib.contextmanager
    def acquire(self, timeout: Optional[float] = None):
        if not self._initialized:
            self.start()
        repl = self._pool.get(timeout=timeout)
        try:
            yield repl
        finally:
            self._pool.put(repl)

    def check_code(self, code: str, timeout_sec: Optional[float] = None) -> REPLResponse:
        """Drop-in replacement for LeanREPL.check_code using pool workers."""
        with self.acquire() as repl:
            return repl.check_code(code, timeout_sec=timeout_sec)

    def close(self):
        with self._lock:
            for repl in self._repls:
                try:
                    repl.close()
                except Exception:
                    pass
            self._repls.clear()
            self._initialized = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

