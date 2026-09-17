"""
MiniF2F Benchmark Runner for AI-Maths-Researcher.
Evaluates autonomous proof search on the official Google DeepMind MiniF2F Lean 4 dataset.
"""

import urllib.request
import re
import argparse
import sys
from pathlib import Path
from typing import List, Tuple

from agent.prover import ProofSearchEngine, ProverConfig
from agent.db import AttemptsDB

MINIF2F_URL = "https://raw.githubusercontent.com/google-deepmind/miniF2F/main/MiniF2F/Test.lean"
LOCAL_CACHE = Path(__file__).resolve().parent / "minif2f_test.lean"

def fetch_minif2f_test() -> str:
    if LOCAL_CACHE.exists():
        return LOCAL_CACHE.read_text(encoding="utf-8")
    print(f"📥 Téléchargement du benchmark MiniF2F Test depuis {MINIF2F_URL}...")
    with urllib.request.urlopen(MINIF2F_URL, timeout=15) as r:
        content = r.read().decode("utf-8")
        LOCAL_CACHE.write_text(content, encoding="utf-8")
        return content

def parse_theorems(content: str) -> List[Tuple[str, str]]:
    """
    Parses theorem declarations (name, full_declaration_statement).
    """
    # Match theorem blocks ending with := by sorry
    pattern = r"(theorem\s+([a-zA-Z0-9_]+)[\s\S]*?:=\s*by\s*\n\s*sorry)"
    matches = re.findall(pattern, content)
    
    results = []
    for full, name in matches:
        # Extract statement up to ':='
        stmt_part = full.split(":=")[0].strip()
        results.append((name, stmt_part))
    return results

def safe_write_file(path: Path, content: str):
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        import subprocess
        subprocess.run(["sh", "-c", f"cat > '{path}'"], input=content, text=True, check=True)

def run_benchmark(limit: int = 50, attempts: int = 3, model: str = "gemini-2.5-flash"):
    content = fetch_minif2f_test()
    theorems = parse_theorems(content)
    selected = theorems[:limit]

    print("\n" + "=" * 60)
    print(f"🏁 Démarrage du Benchmark MiniF2F Lean 4 ({len(selected)} problèmes)")
    print(f"Modèle : {model} | Tentatives max par problème : {attempts}")
    print("=" * 60)

    engine = ProofSearchEngine(config=ProverConfig(max_attempts=attempts, model=model))
    db = AttemptsDB()

    solved_count = 0
    for idx, (name, decl) in enumerate(selected, 1):
        print(f"\n[{idx}/{len(selected)}] Problème : {name}")
        success, code = engine.prove_theorem(decl, problem_name=name)
        if success:
            solved_count += 1
            out_file = Path("problems") / f"minif2f_{name}.lean"
            safe_write_file(out_file, code + "\n")
            print(f"  💾 Sauvegardé dans {out_file}")

    print("\n" + "=" * 60)
    print(f"🏆 RÉSULTAT FINAL BENCHMARK MINIF2F")
    print(f"Problèmes testés  : {len(selected)}")
    print(f"Problèmes résolus : {solved_count} / {len(selected)} ({solved_count / len(selected) * 100:.1f}%)")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="MiniF2F Benchmark Runner")
    parser.add_argument("--limit", type=int, default=10, help="Nombre de problèmes à tester (default: 10)")
    parser.add_argument("--attempts", type=int, default=3, help="Nombre d'essais max par problème (default: 3)")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash", help="Modèle LLM cible")
    args = parser.parse_args()

    run_benchmark(limit=args.limit, attempts=args.attempts, model=args.model)

if __name__ == "__main__":
    main()
