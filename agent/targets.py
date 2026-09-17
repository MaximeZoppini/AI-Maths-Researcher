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
            "verified": self.verified
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
            early_abort=True,
            is_paid_bounty=(target.value_usd > 0)
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
import yaml

class YamlDumper(yaml.SafeDumper):
    pass

def _multiline_str_representer(dumper: yaml.SafeDumper, data: str):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

YamlDumper.add_representer(str, _multiline_str_representer)

def load_targets(path: Path) -> List[Target]:
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    raw = yaml.safe_load(content)
    if not raw or not isinstance(raw, list):
        return []
    return [Target.from_dict(d) for d in raw]

def save_targets(path: Path, targets: List[Target]):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = [t.to_dict() for t in targets]
    content = yaml.dump(raw, Dumper=YamlDumper, default_flow_style=False, allow_unicode=True, sort_keys=False)
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        import subprocess
        subprocess.run(["sh", "-c", f"cat > '{path}'"], input=content, text=True, check=True)


