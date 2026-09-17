"""
Target definition and policy configuration engine for AI-Maths-Researcher.
Translates value, deadline, and empirical p_success into optimal ProverConfig.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from agent.prover import ProverConfig

@dataclass
class Target:
    name: str
    statement: str
    kind: str = "benchmark"                # "benchmark" | "bounty" | "mathlib" | "training"
    value_usd: float = 0.0                 # Prime réelle en USD (0 pour benchmark)
    difficulty_class: str = "unknown"      # mathd | amc | aime | imo | olympiad_other | research
    deadline: Optional[str] = None
    source_url: Optional[str] = None
    submission: Optional[str] = None       # Format / repo cible / instructions
    verified: bool = False                 # Requis : true uniquement si vérifié manuellement ou issu du dataset

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Target":
        raw_v = d.get("verified", False)
        if isinstance(raw_v, str):
            is_verified = raw_v.strip().lower() in ("true", "1", "yes")
        else:
            is_verified = bool(raw_v)
        return cls(
            name=d["name"],
            statement=d["statement"],
            kind=d.get("kind", "benchmark"),
            value_usd=float(d.get("value_usd", 0.0)),
            difficulty_class=d.get("difficulty_class", "unknown"),
            deadline=d.get("deadline"),
            source_url=d.get("source_url"),
            submission=d.get("submission"),
            verified=is_verified
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "statement": self.statement,
            "kind": self.kind,
            "value_usd": self.value_usd,
            "difficulty_class": self.difficulty_class,
            "deadline": self.deadline,
            "source_url": self.source_url,
            "submission": self.submission,
            "verified": "true" if self.verified else "false"
        }

def config_for(target: Target, p_success: float) -> ProverConfig:
    """
    Computes optimal ProverConfig according to economic stakes and empirical p_success:
    - benchmark: cheap, fast (chat, 2 attempts, pass@2, no reasoner, budget $0.10)
    - training: single pass data extraction (chat, 1 attempt, budget $0.05)
    - mathlib: quality and clean code priority (escalation enabled, 4 attempts, budget $0.80)
    - bounty: high stake (escalation enabled, pass@2-4, budget proportional to EV = 10% * value * p_success)
    """
    if target.kind == "benchmark":
        return ProverConfig(
            model="deepseek-chat",
            max_attempts=2,
            pass_k=2,
            enable_escalation=False,
            budget_usd=0.10,
            timeout_per_attempt_sec=25,
            early_abort=True
        )

    elif target.kind == "training":
        return ProverConfig(
            model="deepseek-chat",
            max_attempts=1,
            pass_k=1,
            enable_escalation=False,
            budget_usd=0.05,
            timeout_per_attempt_sec=20,
            early_abort=True
        )

    elif target.kind == "mathlib":
        return ProverConfig(
            model="deepseek-chat",
            max_attempts=4,
            pass_k=1,
            enable_escalation=True,
            budget_usd=0.80,
            timeout_per_attempt_sec=30,
            early_abort=True
        )

    elif target.kind == "bounty":
        # Budget proportionnel à la valeur espérée, encadré entre $0.50 et $5.00
        calculated_budget = target.value_usd * max(0.05, p_success) * 0.10
        bounded_budget = max(0.50, min(5.00, calculated_budget))
        pass_k = 4 if target.value_usd >= 100 else 2

        return ProverConfig(
            model="deepseek-chat",
            max_attempts=4,
            pass_k=pass_k,
            enable_escalation=True,
            budget_usd=bounded_budget,
            timeout_per_attempt_sec=35,
            early_abort=True
        )

    else:
        return ProverConfig(
            model="deepseek-chat",
            max_attempts=3,
            pass_k=1,
            enable_escalation=True,
            budget_usd=0.50,
            timeout_per_attempt_sec=25,
            early_abort=True
        )

from pathlib import Path
from typing import List

def parse_simple_yaml(text: str) -> List[Dict[str, Any]]:
    """Zero-dependency parser for target YAML registry files."""
    items = []
    current = None
    multiline_key = None
    multiline_lines = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        if stripped.startswith('- '):
            if current:
                if multiline_key:
                    current[multiline_key] = '\n'.join(multiline_lines).strip()
                    multiline_key = None
                    multiline_lines = []
                items.append(current)
            current = {}
            line_content = stripped[2:].strip()
            if ':' in line_content:
                k, v = line_content.split(':', 1)
                k = k.strip()
                v = v.strip().strip('\"\'')
                if v == '|':
                    multiline_key = k
                else:
                    current[k] = v
        elif current is not None:
            if multiline_key:
                if line.startswith('    ') or line.startswith('\t\t') or line.startswith('  '):
                    multiline_lines.append(line.strip())
                elif ':' in stripped:
                    current[multiline_key] = '\n'.join(multiline_lines).strip()
                    multiline_key = None
                    multiline_lines = []
                    k, v = stripped.split(':', 1)
                    k = k.strip()
                    v = v.strip().strip('\"\'')
                    if v == '|':
                        multiline_key = k
                    else:
                        current[k] = v
            elif ':' in stripped:
                k, v = stripped.split(':', 1)
                k = k.strip()
                v = v.strip().strip('\"\'')
                if v == '|':
                    multiline_key = k
                else:
                    current[k] = v

    if current:
        if multiline_key:
            current[multiline_key] = '\n'.join(multiline_lines).strip()
        items.append(current)
    return items

def dump_simple_yaml(items: List[Dict[str, Any]]) -> str:
    """Zero-dependency dumper for target YAML registry files."""
    lines = []
    for item in items:
        lines.append(f"- name: {item.get('name', '')}")
        for k, v in item.items():
            if k == 'name':
                continue
            if isinstance(v, str) and '\n' in v:
                lines.append(f"  {k}: |")
                for line in v.splitlines():
                    lines.append(f"    {line}")
            else:
                lines.append(f"  {k}: {v}")
    return '\n'.join(lines) + '\n'

def load_targets(path: Path) -> List[Target]:
    if not path.exists():
        return []
    raw = parse_simple_yaml(path.read_text(encoding="utf-8"))
    return [Target.from_dict(d) for d in raw]

def save_targets(path: Path, targets: List[Target]):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = [t.to_dict() for t in targets]
    content = dump_simple_yaml(raw)
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        import subprocess
        subprocess.run(["sh", "-c", f"cat > '{path}'"], input=content, text=True, check=True)

