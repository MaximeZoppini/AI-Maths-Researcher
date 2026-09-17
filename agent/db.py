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

DB_PATH = Path("/tmp/ai_maths_data/attempts.db")

def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
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

    def get_summary(self) -> Dict[str, Any]:
        with self.conn:
            total_attempts = self.conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            success_count = self.conn.execute("SELECT COUNT(*) FROM attempts WHERE success = 1").fetchone()[0]
            unique_problems = self.conn.execute("SELECT COUNT(DISTINCT problem_name) FROM attempts").fetchone()[0]
            solved_problems = self.conn.execute(
                "SELECT COUNT(DISTINCT problem_name) FROM attempts WHERE success = 1"
            ).fetchone()[0]
            total_cost = self.conn.execute("SELECT COALESCE(SUM(cost_usd), 0.0) FROM attempts").fetchone()[0]
            avg_duration = self.conn.execute("SELECT COALESCE(AVG(duration_ms), 0.0) FROM attempts").fetchone()[0]

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
                "unique_problems": unique_problems,
                "solved_problems": solved_problems,
                "problem_solve_rate": (solved_problems / unique_problems) if unique_problems > 0 else 0.0,
                "total_cost_usd": total_cost,
                "avg_duration_ms": avg_duration,
                "models": models
            }
