"""
SQLite Database for AI-Maths-Researcher Proof Attempts.
Tracks problems, prompts, model outputs, compiler errors, iterations, latency, and costs.
Stores persistent DB in /tmp/ai_maths_data/attempts.db to ensure full POSIX ACID locking on macOS.
"""

import sqlite3
import datetime
import json
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = (Path(__file__).resolve().parent.parent / "data" / "attempts.db").resolve()
BACKUP_DIR = (Path(__file__).resolve().parent.parent / "data" / "backups").resolve()
PERSISTENT_STORE = Path("/var/tmp/ai_maths_data/attempts.db")

def classify_problem(name: str) -> str:
    n = name.lower()
    if "mathd" in n:
        return "mathd"
    elif "amc" in n:
        return "amc"
    elif "aime" in n:
        return "aime"
    elif "imo" in n or "imoshortlist" in n:
        return "imo"
    elif any(k in n for k in ["algebra", "numbertheory", "induction"]):
        return "olympiad_other"
    else:
        return "other"

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

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=10000;")
    except Exception:
        pass

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
            cost_usd REAL DEFAULT 0.0,
            difficulty_class TEXT DEFAULT 'unknown'
        );
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_attempts_problem ON attempts(problem_name);
        """)

        # Migration: ajouter difficulty_class si absente et backfill automatique
        cols = [col[1] for col in conn.execute("PRAGMA table_info(attempts)").fetchall()]
        if "difficulty_class" not in cols:
            conn.execute("ALTER TABLE attempts ADD COLUMN difficulty_class TEXT DEFAULT 'unknown';")
        
        # Backfill des entrées 'unknown' ou nulles
        rows_to_backfill = conn.execute("SELECT id, problem_name FROM attempts WHERE difficulty_class IS NULL OR difficulty_class = 'unknown'").fetchall()
        for r in rows_to_backfill:
            cls = classify_problem(r["problem_name"])
            conn.execute("UPDATE attempts SET difficulty_class = ? WHERE id = ?", (cls, r["id"]))

    return conn

class AttemptsDB:
    _lock = threading.Lock()

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
        difficulty_class: Optional[str] = None
    ) -> int:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        diff_class = difficulty_class or classify_problem(problem_name)
        with self._lock:
            with self.conn:
                cursor = self.conn.execute(
                    """
                    INSERT INTO attempts (
                        timestamp, problem_name, iteration, model, prompt, candidate_code,
                        success, compiler_errors, unsolved_goals, duration_ms,
                        prompt_tokens, completion_tokens, cost_usd, difficulty_class
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        now, problem_name, iteration, model, prompt, candidate_code,
                        1 if success else 0, compiler_errors, unsolved_goals, duration_ms,
                        prompt_tokens, completion_tokens, cost_usd, diff_class
                    )
                )
                return cursor.lastrowid

    def backup(self) -> Path:
        with self._lock:
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

    def get_success_rates_by_class(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculates p_success per difficulty class (mathd, amc, aime, imo, olympiad_other)
        based on distinct problem resolutions.
        """
        with self.conn:
            rows = self.conn.execute("""
                SELECT difficulty_class,
                       COUNT(DISTINCT problem_name) AS attempted,
                       SUM(solved) AS solved
                FROM (
                    SELECT problem_name, difficulty_class, MAX(success) AS solved
                    FROM attempts
                    WHERE problem_name NOT LIKE '%_step%'
                    GROUP BY problem_name
                )
                GROUP BY difficulty_class
                ORDER BY attempted DESC;
            """).fetchall()

            res = {}
            for r in rows:
                attempted = r["attempted"]
                solved = r["solved"] or 0
                p_succ = (solved / attempted) if attempted > 0 else 0.0
                res[r["difficulty_class"]] = {
                    "attempted": attempted,
                    "solved": solved,
                    "p_success": p_succ
                }
            return res
