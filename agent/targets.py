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
    budget_unlocked: bool = False          # Déblocage de budget explicite accordé via Telegram (/approve)
    bounty_hint: bool = False              # Signal de bounty potentiel détecté par mots-clés
    offpeak_only: bool = False             # Exécution réservée aux heures creuses DeepSeek (-50%)
    approval_stage: str = "none"           # none -> approved -> confirmed | rejected | denied
    approved_at: Optional[str] = None      # Horodatage ISO de l'approbation d'autoformalisation
    confirmed_at: Optional[str] = None     # Horodatage ISO de la confirmation de recherche de preuve
    natural_language: Optional[str] = None # Énoncé original en langage naturel
    round_trip_translation: Optional[str] = None # Rétro-traduction Lean -> langage naturel
    round_trip_score: Optional[float] = None     # Score d'équivalence sémantique (0.0 - 1.0)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Target":
        raw_v = d.get("verified", False)
        if isinstance(raw_v, str):
            is_verified = raw_v.strip().lower() in ("true", "1", "yes")
        else:
            is_verified = bool(raw_v)
        raw_b = d.get("budget_unlocked", False)
        if isinstance(raw_b, str):
            is_unlocked = raw_b.strip().lower() in ("true", "1", "yes")
        else:
            is_unlocked = bool(raw_b)

        raw_bh = d.get("bounty_hint", False)
        if isinstance(raw_bh, str):
            bounty_hint = raw_bh.strip().lower() in ("true", "1", "yes")
        else:
            bounty_hint = bool(raw_bh)

        raw_val = float(d.get("value_usd", 0.0))
        raw_op = d.get("offpeak_only", None)
        if raw_op is not None:
            if isinstance(raw_op, str):
                offpeak_only = raw_op.strip().lower() in ("true", "1", "yes")
            else:
                offpeak_only = bool(raw_op)
        else:
            offpeak_only = (raw_val > 0)

        approval_stage = str(d.get("approval_stage", "none")).strip().lower()
        if approval_stage not in ("none", "approved", "confirmed", "rejected", "denied"):
            approval_stage = "none"

        raw_score = d.get("round_trip_score")
        score = float(raw_score) if raw_score is not None else None

        return cls(
            name=d["name"],
            statement=d["statement"],
            kind=d.get("kind", "benchmark"),
            value_usd=raw_val,
            difficulty_class=d.get("difficulty_class", "unknown"),
            deadline=d.get("deadline"),
            source_url=d.get("source_url"),
            submission=d.get("submission"),
            verified=is_verified,
            budget_unlocked=is_unlocked,
            bounty_hint=bounty_hint,
            offpeak_only=offpeak_only,
            approval_stage=approval_stage,
            approved_at=d.get("approved_at"),
            confirmed_at=d.get("confirmed_at"),
            natural_language=d.get("natural_language"),
            round_trip_translation=d.get("round_trip_translation"),
            round_trip_score=score
        )

    def to_dict(self) -> Dict[str, Any]:
        d = {
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
        if self.budget_unlocked:
            d["budget_unlocked"] = True
        if self.bounty_hint:
            d["bounty_hint"] = True
        if self.offpeak_only:
            d["offpeak_only"] = True
        if self.approval_stage and self.approval_stage != "none":
            d["approval_stage"] = self.approval_stage
        if self.approved_at:
            d["approved_at"] = self.approved_at
        if self.confirmed_at:
            d["confirmed_at"] = self.confirmed_at
        if self.natural_language:
            d["natural_language"] = self.natural_language
        if self.round_trip_translation:
            d["round_trip_translation"] = self.round_trip_translation
        if self.round_trip_score is not None:
            d["round_trip_score"] = self.round_trip_score
        return d

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
            model="deepseek-flash",
            max_attempts=2,
            pass_k=2,
            enable_escalation=False,
            budget_usd=0.10,
            timeout_per_attempt_sec=25,
            early_abort=True
        )

    elif target.kind == "training":
        return ProverConfig(
            model="deepseek-flash",
            max_attempts=1,
            pass_k=1,
            enable_escalation=False,
            budget_usd=0.05,
            timeout_per_attempt_sec=20,
            early_abort=True
        )

    elif target.kind == "mathlib":
        return ProverConfig(
            model="deepseek-flash",
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
            model="deepseek-flash",
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
            model="deepseek-flash",
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


