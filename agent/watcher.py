#!/usr/bin/env python3
"""
Whitelisted GitHub Issues Watcher for AI-Maths-Researcher.
Monitors manually approved repositories for new formalization issues/bounties.
Security guarantee:
- Consumes ONLY whitelisted repositories configured in targets/watchlist.yaml.
- Created draft targets are ALWAYS marked 'verified: false'.
- Never executes, formalizes, or submits code from unverified issues.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from agent.targets import Target, load_targets, save_targets

ROOT_DIR = Path(__file__).resolve().parent.parent
WATCHLIST_PATH = ROOT_DIR / "targets" / "watchlist.yaml"
REGISTRY_PATH = ROOT_DIR / "targets" / "registry.yaml"
STATE_PATH = ROOT_DIR / "data" / "watcher_state.json"

def load_watchlist(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Loads approved repositories from watchlist.yaml without executing arbitrary data."""
    target_path = path or WATCHLIST_PATH
    if not target_path.exists():
        return []
    content = target_path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    raw = yaml.safe_load(content)
    if not raw or not isinstance(raw, list):
        return []
    entries = []
    for item in raw:
        repo = item.get("repo")
        if repo and "/" in repo:
            labels_raw = item.get("labels", [])
            if isinstance(labels_raw, str):
                labels_clean = [l.strip("[]'\" ") for l in labels_raw.split(",") if l.strip("[]'\" ")]
            else:
                labels_clean = list(labels_raw)
            entries.append({
                "repo": repo.strip(),
                "labels": labels_clean,
                "kind_hint": item.get("kind_hint", "bounty")
            })
    return entries

def load_state() -> Dict[str, Any]:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_run_iso": None, "repos": {}}

def save_state(state: Dict[str, Any]):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(state, indent=2)
    try:
        STATE_PATH.write_text(content, encoding="utf-8")
    except PermissionError:
        import subprocess
        subprocess.run(["sh", "-c", f"cat > '{STATE_PATH}'"], input=content, text=True, check=True)

def fetch_repo_issues(repo: str, labels: List[str], since_iso: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches public issues from GitHub REST API."""
    params = {"state": "open", "per_page": 20}
    if labels:
        params["labels"] = ",".join(labels)
    if since_iso:
        params["since"] = since_iso

    url = f"https://api.github.com/repos/{repo}/issues?{urllib.parse.urlencode(params)}"
    headers = {
        "User-Agent": "AI-Maths-Researcher-Watcher/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            # Filtrer les pull requests (l'API issues retourne aussi les PRs)
            issues = [item for item in data if item.get("pull_request") is None]
            return issues
    except Exception as e:
        print(f"⚠️ Erreur lors de la requête GitHub sur '{repo}' : {e}")
        return []

def check_watchlist(
    force: bool = False,
    throttle_sec: int = 86400,
    watchlist_path: Optional[Path] = None,
    registry_path: Optional[Path] = None
) -> List[Target]:
    """
    Executes a watcher pass on the whitelisted sources.
    Throttled to once every 24h by default unless force=True.
    """
    w_path = watchlist_path or WATCHLIST_PATH
    r_path = registry_path or REGISTRY_PATH
    watchlist = load_watchlist(w_path)
    if not watchlist:
        print("ℹ️ Watchlist vide. Aucune source à surveiller.")
        return []

    state = load_state()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    last_run_str = state.get("last_run_iso")

    if not force and last_run_str:
        try:
            last_run = datetime.datetime.fromisoformat(last_run_str)
            elapsed = (now_utc - last_run).total_seconds()
            if elapsed < throttle_sec:
                remaining_hours = (throttle_sec - elapsed) / 3600
                print(f"⏱️ Watcher en veille (prochain passage dans {remaining_hours:.1f} h).")
                return []
        except Exception:
            pass

    existing_targets = load_targets(REGISTRY_PATH)
    existing_urls = {t.source_url for t in existing_targets if t.source_url}
    existing_names = {t.name for t in existing_targets}

    new_draft_targets: List[Target] = []

    for src in watchlist:
        repo = src["repo"]
        labels = src["labels"]
        kind_hint = src["kind_hint"]

        last_repo_check = state.get("repos", {}).get(repo)
        issues = fetch_repo_issues(repo, labels, since_iso=last_repo_check)
        print(f"🔍 Source '{repo}' : {len(issues)} issue(s) relevée(s).")

        for issue in issues:
            html_url = issue.get("html_url", "")
            title = issue.get("title", "Sans titre")
            number = issue.get("number", 0)

            if html_url in existing_urls:
                continue

            slug_name = f"issue_{repo.replace('/', '_')}_{number}"
            if slug_name in existing_names:
                continue

            # RÈGLE ABSOLUE : Donnée brute, verified: false, pas d'interprétation
            draft_target = Target(
                name=slug_name,
                statement=f"-- Source: {html_url}\n-- Titre: {title}\n-- En attente de formulation Lean et validation humaine\n",
                kind=kind_hint,
                value_usd=0.0,
                difficulty_class="unknown",
                deadline=None,
                source_url=html_url,
                submission=f"Issue #{number}: {title}",
                verified=False
            )

            new_draft_targets.append(draft_target)
            existing_urls.add(html_url)
            existing_names.add(slug_name)

        if "repos" not in state:
            state["repos"] = {}
        state["repos"][repo] = now_utc.isoformat()

    if new_draft_targets:
        print(f"📝 {len(new_draft_targets)} nouvelle(s) cible(s) brouillon ajoutée(s) au registre avec 'verified: false'.")
        updated_targets = existing_targets + new_draft_targets
        save_targets(REGISTRY_PATH, updated_targets)
    else:
        print("✅ Aucune nouvelle issue détectée sur les sources surveillées.")

    state["last_run_iso"] = now_utc.isoformat()
    save_state(state)
    return new_draft_targets

def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI-Maths-Researcher Whitelisted Watcher")
    parser.add_argument("--force", action="store_true", help="Forcer l'exécution sans attendre le délai de throttle (24h)")
    args = parser.parse_args()

    new_items = check_watchlist(force=args.force)
    print(f"Bilan : {len(new_items)} nouvelle(s) cible(s) en attente de validation.")

if __name__ == "__main__":
    main()
