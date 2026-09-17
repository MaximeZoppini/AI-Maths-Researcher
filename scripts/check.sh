#!/usr/bin/env bash
set -e

echo "=== [1/2] Compilation du package principal Lean 4 ==="
lake build

echo "=== [2/2] Audit formel mathématique des axiomes (#print axioms) ==="
python3 scripts/audit_axioms.py
