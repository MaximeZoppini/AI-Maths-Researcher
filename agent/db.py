"""
SQLite Database for AI-Maths-Researcher Proof Attempts.
Tracks problems, prompts, model outputs, compiler errors, iterations, latency, and costs.
Stores persistent DB in /tmp/ai_maths_data/attempts.db to ensure full POSIX ACID locking on macOS.
"""

import sqlite3
import datetime
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path("data/attempts.db")
BACKUP_DIR = Path("data/backups")
PERSISTENT_STORE = Path("/var/tmp/ai_maths_data/attempts.db")

def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    PERSISTENT_STORE.parent.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Under macOS Documents sandbox, symlink data/attempts.db -> /var/tmp/...
    if str(db_path) == str(DB_PATH) and not db_path.exists():
        if not PERSISTENT_STORE.exists():
            PERSISTENT_STORE.touch()
        try:
            db_path.symlink_to(PERSISTENT_STORE)
        except Exception:
            pass

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            problem_name TEXT NOT NULL,
            iteration INTEGER NOT NULL,
            model TEXT NOT NULL,
            prompt TEXT NOT NULL,
            candidate_code TEXT NOT NULL,
            success INTEGER NOT NULL,
            compiler_errors TEXT,
            unsolved_goals TEXT,
            duration_ms REAL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0.0
        );
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_attempts_problem ON attempts(problem_name);
        """)
    return conn

class AttemptsDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = init_db(db_path)

    def record_attempt(
        self,
        problem_name: str,
        iteration: int,
        model: str,
        prompt: str,
        candidate_code: str,
        success: bool,
        compiler_errors: Optional[str] = None,
        unsolved_goals: Optional[str] = None,
        duration_ms: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> int:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO attempts (
                    timestamp, problem_name, iteration, model, prompt, candidate_code,
                    success, compiler_errors, unsolved_goals, duration_ms,
                    prompt_tokens, completion_tokens, cost_usd
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now, problem_name, iteration, model, prompt, candidate_code,
                    1 if success else 0, compiler_errors, unsolved_goals, duration_ms,
                    prompt_tokens, completion_tokens, cost_usd
                )
            )
            return cursor.lastrowid

    def backup(self) -> Path:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"attempts_{timestamp}.sql"
        latest_file = BACKUP_DIR / "attempts_latest.sql"
        try:
            dump = "\n".join(self.conn.iterdump())
            backup_file.write_text(dump, encoding="utf-8")
            latest_file.write_text(dump, encoding="utf-8")
            print(f"💾 Sauvegarde SQLite créée : {backup_file}")
            return backup_file
        except Exception as e:
            # Fallback to /var/tmp if permissions fail
            alt_backup = PERSISTENT_STORE.parent / f"attempts_{timestamp}.sql"
            dump = "\n".join(self.conn.iterdump())
            alt_backup.write_text(dump, encoding="utf-8")
            print(f"💾 Sauvegarde SQLite alternative créée : {alt_backup} (erreur: {e})")
            return alt_backup

    def get_summary(self) -> Dict[str, Any]:
        with self.conn:
            total_attempts = self.conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            success_count = self.conn.execute("SELECT COUNT(*) FROM attempts WHERE success = 1").fetchone()[0]
            total_cost = self.conn.execute("SELECT COALESCE(SUM(cost_usd), 0.0) FROM attempts").fetchone()[0]
            avg_duration = self.conn.execute("SELECT COALESCE(AVG(duration_ms), 0.0) FROM attempts").fetchone()[0]

            # Distinguer les problèmes de base des sous-lemmes (_stepN)
            all_problem_rows = self.conn.execute("SELECT problem_name, success FROM attempts").fetchall()
            base_problems = set()
            solved_base = set()
            sub_lemmas = set()
            solved_sub_lemmas = set()

            for r in all_problem_rows:
                name = r["problem_name"]
                succ = (r["success"] == 1)
                if "_step" in name:
                    sub_lemmas.add(name)
                    if succ:
                        solved_sub_lemmas.add(name)
                else:
                    base_problems.add(name)
                    if succ:
                        solved_base.add(name)

            model_rows = self.conn.execute("""
                SELECT model,
                       COUNT(*) as total,
                       SUM(success) as successes,
                       COALESCE(SUM(cost_usd), 0.0) as cost
                FROM attempts
                GROUP BY model
            """).fetchall()

            models = []
            for r in model_rows:
                models.append({
                    "model": r["model"],
                    "total": r["total"],
                    "successes": r["successes"] or 0,
                    "rate": (r["successes"] or 0) / r["total"] if r["total"] > 0 else 0.0,
                    "cost": r["cost"]
                })

            return {
                "total_attempts": total_attempts,
                "success_count": success_count,
                "attempt_success_rate": (success_count / total_attempts) if total_attempts > 0 else 0.0,
                "base_problems_count": len(base_problems),
                "solved_base_count": len(solved_base),
                "base_solve_rate": (len(solved_base) / len(base_problems)) if base_problems else 0.0,
                "sub_lemmas_count": len(sub_lemmas),
                "solved_sub_lemmas_count": len(solved_sub_lemmas),
                "total_cost_usd": total_cost,
                "avg_duration_ms": avg_duration,
                "models": models
            }
