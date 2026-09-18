#!/usr/bin/env python3
"""
Tests unitaires et d'intégration pour la TÂCHE 13 de MISSION.md:
Boucle bounty complète : proposition -> accord Telegram -> autoformalisation -> confirmation -> résolution heures creuses.
"""

import os
import sys
import unittest
import tempfile
import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from agent.targets import Target, load_targets, save_targets
from agent.watcher import check_watchlist
from agent.notifier import TelegramNotifier
from agent.prover import (
    is_deepseek_offpeak,
    get_next_offpeak_window_utc,
    get_next_offpeak_window_str
)
from scripts.daemon import run_daemon


class TestTask13BountyLoop(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.registry_file = self.temp_path / "registry.yaml"
        self.queue_file = self.temp_path / "queue.yaml"
        self.watchlist_file = self.temp_path / "watchlist.yaml"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_watcher_detects_bounty_hint_without_fabricating_value(self):
        """Critère 13.1 : Mots-clés (bounty, prize, reward, $) posent bounty_hint: true sans déduire de montant."""
        mock_issues = [
            {
                "html_url": "https://github.com/org/repo/issues/101",
                "title": "Huge $500 reward for proving Goldbach partial",
                "number": 101,
                "labels": [{"name": "math"}],
                "body": "Formalize this problem in Lean 4"
            },
            {
                "html_url": "https://github.com/org/repo/issues/102",
                "title": "Fix parser precedence in tactic combinator",
                "number": 102,
                "labels": [{"name": "tactic"}],
                "body": "Fix this tactic bug"
            }
        ]
        watchlist_content = "- repo: org/repo\n  labels: []\n  kind_hint: bounty\n"
        self.watchlist_file.write_text(watchlist_content, encoding="utf-8")

        with patch("agent.watcher.fetch_repo_issues", return_value=mock_issues), \
             patch("agent.watcher.STATE_PATH", self.temp_path / "state.json"):
            targets = check_watchlist(
                force=True,
                watchlist_path=self.watchlist_file,
                registry_path=self.registry_file
            )

        self.assertEqual(len(targets), 2)
        bounty_target = next(t for t in targets if "101" in t.name)
        regular_target = next(t for t in targets if "102" in t.name)

        # Vérification du signal
        self.assertTrue(bounty_target.bounty_hint)
        self.assertFalse(regular_target.bounty_hint)

        # RÈGLE ABSOLUE : INTERDICTION D'INVENTER UN MONTANT
        self.assertEqual(bounty_target.value_usd, 0.0)
        self.assertFalse(bounty_target.verified)
        self.assertEqual(bounty_target.approval_stage, "none")
        self.assertIn("Goldbach", bounty_target.natural_language)

    def test_bounty_proposal_sound_notification(self):
        """Critère 1 : Fiche avec bounty_hint: true -> notification SONORE émise."""
        notifier = TelegramNotifier(bot_token="fake_token", chat_id="123456")

        with patch.object(notifier, "send_message") as mock_send:
            notifier.notify_bounty_proposal(
                target_name="issue_bounty_42",
                title="Solve IMO 2026 Problem 6",
                repo="leanprover-community/mathlib4",
                url="https://github.com/issue/42"
            )
            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            text = args[0]
            # silent doit être False pour une notification SONORE
            self.assertFalse(kwargs.get("silent", True))
            self.assertIn("/approve_issue_bounty_42", text)
            self.assertIn("/deny_issue_bounty_42", text)

    def test_step1_approve_from_authorized_chat(self):
        """Critère 2 & 3 : /approve depuis bon chat_id débloque formalisation seule ; chat inconnu rejeté."""
        notifier = TelegramNotifier(bot_token="fake_token", chat_id="123456")

        # Cas A : bon chat_id
        mock_response_authorized = {
            "ok": True,
            "result": [
                {
                    "update_id": 10,
                    "message": {
                        "chat": {"id": 123456},
                        "text": "/approve_target_gold"
                    }
                }
            ]
        }
        with patch("urllib.request.urlopen") as mock_url, \
             patch.object(notifier, "send_message") as mock_send:
            mock_url.return_value.__enter__.return_value.read.return_value = str(mock_response_authorized).replace("'", '"').replace("True", "true").encode("utf-8")
            res = notifier.poll_approvals(pending_approvals=["target_gold"])
            self.assertIsNotNone(res)
            self.assertEqual(res.get("action"), "approve")
            self.assertEqual(res.get("target_name"), "target_gold")
            mock_send.assert_called_once()
            self.assertIn("Autoformalisation autorisée", mock_send.call_args[0][0])

        # Cas B : mauvais chat_id -> strictement rejeté
        mock_response_unauthorized = {
            "ok": True,
            "result": [
                {
                    "update_id": 11,
                    "message": {
                        "chat": {"id": 999999},
                        "text": "/approve_target_gold"
                    }
                }
            ]
        }
        with patch("urllib.request.urlopen") as mock_url, \
             patch.object(notifier, "send_message") as mock_send:
            mock_url.return_value.__enter__.return_value.read.return_value = str(mock_response_unauthorized).replace("'", '"').replace("True", "true").encode("utf-8")
            res = notifier.poll_approvals(pending_approvals=["target_gold"])
            self.assertIsNone(res)
            mock_send.assert_not_called()

        # Cas C : texte libre depuis bon chat_id -> consigné et ignoré
        mock_response_freetext = {
            "ok": True,
            "result": [
                {
                    "update_id": 12,
                    "message": {
                        "chat": {"id": 123456},
                        "text": "Vas-y prouve ce théorème s'il te plaît"
                    }
                }
            ]
        }
        with patch("urllib.request.urlopen") as mock_url, \
             patch.object(notifier, "send_message") as mock_send:
            mock_url.return_value.__enter__.return_value.read.return_value = str(mock_response_freetext).replace("'", '"').replace("True", "true").encode("utf-8")
            res = notifier.poll_approvals(pending_approvals=["target_gold"])
            self.assertIsNone(res)
            mock_send.assert_not_called()

    def test_step2_confirm_and_reject_actions(self):
        """Critère 2 : /confirm_<nom> débloque la preuve, /reject_<nom> rejette l'énoncé."""
        notifier = TelegramNotifier(bot_token="fake_token", chat_id="123456")

        # Test /confirm
        mock_resp_confirm = {
            "ok": True,
            "result": [
                {
                    "update_id": 20,
                    "message": {
                        "chat": {"id": 123456},
                        "text": "/confirm_target_gold"
                    }
                }
            ]
        }
        with patch("urllib.request.urlopen") as mock_url, \
             patch.object(notifier, "send_message") as mock_send:
            mock_url.return_value.__enter__.return_value.read.return_value = str(mock_resp_confirm).replace("'", '"').replace("True", "true").encode("utf-8")
            res = notifier.poll_approvals(pending_confirms=["target_gold"])
            self.assertIsNotNone(res)
            self.assertEqual(res.get("action"), "confirm")
            self.assertEqual(res.get("target_name"), "target_gold")
            self.assertIn("Recherche de preuve débloquée", mock_send.call_args[0][0])

        # Test /reject
        mock_resp_reject = {
            "ok": True,
            "result": [
                {
                    "update_id": 21,
                    "message": {
                        "chat": {"id": 123456},
                        "text": "/reject_target_gold"
                    }
                }
            ]
        }
        with patch("urllib.request.urlopen") as mock_url, \
             patch.object(notifier, "send_message") as mock_send:
            mock_url.return_value.__enter__.return_value.read.return_value = str(mock_resp_reject).replace("'", '"').replace("True", "true").encode("utf-8")
            res = notifier.poll_approvals(pending_confirms=["target_gold"])
            self.assertIsNotNone(res)
            self.assertEqual(res.get("action"), "reject")
            self.assertEqual(res.get("target_name"), "target_gold")
            self.assertIn("Énoncé rejeté", mock_send.call_args[0][0])

    def test_offpeak_calculation_and_gate(self):
        """Critère 4 : Fenêtres heures creuses officielles et différé sans dépense hors fenêtre."""
        # 1. Week-end entier = heures creuses
        saturday = datetime.datetime(2026, 9, 19, 12, 0, tzinfo=datetime.timezone.utc)
        sunday = datetime.datetime(2026, 9, 20, 3, 0, tzinfo=datetime.timezone.utc)
        self.assertTrue(is_deepseek_offpeak(saturday))
        self.assertTrue(is_deepseek_offpeak(sunday))
        self.assertEqual(get_next_offpeak_window_str(saturday), "actuellement ouvert (-50%)")

        # 2. Semaine pic 1 (01:00-04:00 UTC) -> heures pleines, ouverture à 04:00 UTC
        wednesday_peak1 = datetime.datetime(2026, 9, 16, 2, 30, tzinfo=datetime.timezone.utc)
        self.assertFalse(is_deepseek_offpeak(wednesday_peak1))
        self.assertEqual(get_next_offpeak_window_utc(wednesday_peak1).hour, 4)
        self.assertEqual(get_next_offpeak_window_str(wednesday_peak1), "04:00 UTC")

        # 3. Semaine pic 2 (06:00-10:00 UTC) -> heures pleines, ouverture à 10:00 UTC
        wednesday_peak2 = datetime.datetime(2026, 9, 16, 7, 15, tzinfo=datetime.timezone.utc)
        self.assertFalse(is_deepseek_offpeak(wednesday_peak2))
        self.assertEqual(get_next_offpeak_window_utc(wednesday_peak2).hour, 10)
        self.assertEqual(get_next_offpeak_window_str(wednesday_peak2), "10:00 UTC")

        # 4. Semaine en dehors des pics (ex: 15:00 UTC) -> heures creuses
        wednesday_offpeak = datetime.datetime(2026, 9, 16, 15, 0, tzinfo=datetime.timezone.utc)
        self.assertTrue(is_deepseek_offpeak(wednesday_offpeak))
        self.assertEqual(get_next_offpeak_window_str(wednesday_offpeak), "actuellement ouvert (-50%)")

    def test_daemon_defers_offpeak_target_when_in_peak(self):
        """Critère 4 : Cible avec offpeak_only différée hors fenêtre creuse avec zéro dépense."""
        target = Target(
            name="bounty_test_target",
            statement="theorem foo : 1 = 1 := by sorry",
            kind="bounty",
            value_usd=50.0,
            verified=True,
            offpeak_only=True,
            approval_stage="confirmed"
        )
        save_targets(self.queue_file, [target])

        with patch("scripts.daemon.QUEUE_PATH", self.queue_file), \
             patch("scripts.daemon.REGISTRY_PATH", self.registry_file), \
             patch("scripts.daemon.is_deepseek_offpeak", return_value=False), \
             patch("scripts.daemon.ProofSearchEngine") as mock_engine, \
             patch("scripts.daemon.generate_dashboard"):

            # Exécuter run_daemon avec run_once=True
            run_daemon(run_once=True, auto_commit=False)

            # Doit être différé sans AUCUN appel au moteur de preuve
            mock_engine.assert_not_called()

            # La cible reste intacte dans la file
            loaded = load_targets(self.queue_file)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].name, "bounty_test_target")

    def test_persistence_across_restarts(self):
        """Critère 5 : Conservation intégrale des états et horodatages dans le YAML via PyYAML."""
        target = Target(
            name="bounty_complex_123",
            statement="theorem bounty_complex_123 (n : ℕ) : n + 0 = n := by sorry",
            kind="bounty",
            value_usd=100.0,
            verified=True,
            bounty_hint=True,
            offpeak_only=True,
            approval_stage="confirmed",
            approved_at="2026-09-18T10:00:00+00:00",
            confirmed_at="2026-09-18T10:15:00+00:00",
            natural_language="Prove that adding zero to any natural number yields the same number.",
            round_trip_translation="For any natural number n, n + 0 equals n.",
            round_trip_score=0.98
        )

        yaml_file = self.temp_path / "targets_test.yaml"
        save_targets(yaml_file, [target])

        # Relire depuis le disque
        loaded = load_targets(yaml_file)
        self.assertEqual(len(loaded), 1)
        lt = loaded[0]

        self.assertEqual(lt.name, "bounty_complex_123")
        self.assertTrue(lt.verified)
        self.assertTrue(lt.bounty_hint)
        self.assertTrue(lt.offpeak_only)
        self.assertEqual(lt.approval_stage, "confirmed")
        self.assertEqual(lt.approved_at, "2026-09-18T10:00:00+00:00")
        self.assertEqual(lt.confirmed_at, "2026-09-18T10:15:00+00:00")
        self.assertEqual(lt.natural_language, "Prove that adding zero to any natural number yields the same number.")
        self.assertEqual(lt.round_trip_translation, "For any natural number n, n + 0 equals n.")
        self.assertAlmostEqual(lt.round_trip_score, 0.98)


if __name__ == "__main__":
    unittest.main()
