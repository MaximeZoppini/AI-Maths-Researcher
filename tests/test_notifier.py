#!/usr/bin/env python3
"""
Unit and Integration Tests for Task 11: Telegram Notifier & Secure Approval Channel.
Validates:
1. Outbound notifications (silent for proofs/watcher/digest, loud for gates/approvals).
2. Inbound security (rejecting unauthorized chat_id, rejecting arbitrary text and commands).
3. Budget approval workflow (/approve and /deny matching pending targets).
4. Network fault tolerance (smooth operation when Telegram API is unreachable).
5. State persistence (last_update_id).
6. Target serialization with budget_unlocked.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
from pathlib import Path
import urllib.error

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from agent.notifier import TelegramNotifier
from agent.targets import Target

class TestTelegramNotifier(unittest.TestCase):

    def setUp(self):
        self.bot_token = "123456:TEST_TOKEN"
        self.chat_id = "8486359334"
        self.notifier = TelegramNotifier(bot_token=self.bot_token, chat_id=self.chat_id)
        # Use a temporary state file for tests
        self.test_state_file = ROOT_DIR / "data" / "test_telegram_state.json"
        self.notifier.state_file = self.test_state_file
        if self.test_state_file.exists():
            self.test_state_file.unlink()

    def tearDown(self):
        if self.test_state_file.exists():
            self.test_state_file.unlink()

    @patch("urllib.request.urlopen")
    def test_outbound_silent_notifications(self, mock_urlopen):
        """Preuves, Watcher et Digest doivent être envoyés avec disable_notification: True (silencieux)."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"ok": True, "result": {"message_id": 101}}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # 1. Preuve certifiée
        ok = self.notifier.notify_proof_certified("mathd_algebra_392", "mathd", 0.005, 2)
        self.assertTrue(ok)
        req_sent = mock_urlopen.call_args[0][0]
        payload = json.loads(req_sent.data.decode("utf-8"))
        self.assertTrue(payload["disable_notification"], "La notification de preuve doit être silencieuse")
        self.assertIn("mathd_algebra_392", payload["text"])

        # 2. Watcher
        ok = self.notifier.notify_watcher_new_targets([{"title": "New Lemma", "url": "https://github.com/test"}])
        self.assertTrue(ok)
        payload = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
        self.assertTrue(payload["disable_notification"], "La notification du watcher doit être silencieuse")

        # 3. Digest
        ok = self.notifier.send_daily_digest(db=None, queue_targets=[], balance=1.50)
        self.assertTrue(ok)
        payload = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
        self.assertTrue(payload["disable_notification"], "Le digest quotidien doit être silencieux")

    @patch("urllib.request.urlopen")
    def test_outbound_loud_alarms(self, mock_urlopen):
        """Gates et Demandes d'approbation de budget doivent être SONORES (disable_notification: False)."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"ok": True, "result": {"message_id": 102}}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # 1. Gate déclenchée
        ok = self.notifier.notify_gate_triggered("FICHIER STOP", "Arrêt immédiat")
        self.assertTrue(ok)
        payload = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
        self.assertFalse(payload["disable_notification"], "L'alerte gate doit être SONORE")

        # 2. Demande d'autorisation de budget
        ok = self.notifier.request_budget_approval("bounty_test_target", 50.0, 0.40, 0.45)
        self.assertTrue(ok)
        payload = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
        self.assertFalse(payload["disable_notification"], "La demande d'autorisation de budget doit être SONORE")
        self.assertIn("/approve_bounty_test_target", payload["text"])

    @patch("urllib.request.urlopen")
    def test_security_reject_unauthorized_chat_id(self, mock_urlopen):
        """Les messages provenant d'un chat_id autre que TELEGRAM_CHAT_ID doivent être strictement rejetés."""
        fake_updates = {
            "ok": True,
            "result": [
                {
                    "update_id": 1001,
                    "message": {
                        "message_id": 1,
                        "chat": {"id": 999999999},  # Intruder chat id!
                        "from": {"id": 999999999},
                        "text": "/approve_target_secret"
                    }
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(fake_updates).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        result = self.notifier.poll_approvals(["target_secret"])
        self.assertIsNone(result, "Un ordre venant d'un chat_id non autorisé ne doit JAMAIS être accepté")

    @patch("urllib.request.urlopen")
    def test_security_reject_arbitrary_commands_and_free_text(self, mock_urlopen):
        """Tout texte libre ou commande hors /approve_<nom> et /deny_<nom> pour cible en attente doit être ignoré."""
        unauthorized_texts = [
            "Bonjour Marcus",
            "/stop",
            "/start",
            "/help",
            "/approve",  # Manque le nom de la cible
            "/approve_other_target",  # Cible non en attente
            "rm -rf /",
            "/unknown_command"
        ]

        for text in unauthorized_texts:
            fake_updates = {
                "ok": True,
                "result": [
                    {
                        "update_id": 2000,
                        "message": {
                            "message_id": 2,
                            "chat": {"id": int(self.chat_id)},
                            "from": {"id": int(self.chat_id)},
                            "text": text
                        }
                    }
                ]
            }
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(fake_updates).encode("utf-8")
            mock_resp.__enter__.return_value = mock_resp
            mock_urlopen.return_value = mock_resp

            result = self.notifier.poll_approvals(["valid_pending_target"])
            self.assertIsNone(result, f"Le texte '{text}' aurait dû être ignoré")

    @patch("urllib.request.urlopen")
    def test_status_command_processing(self, mock_urlopen):
        """La commande /status doit renvoyer le rapport KPIs et l'URL Tailscale du dashboard."""
        status_updates = {
            "ok": True,
            "result": [
                {
                    "update_id": 2500,
                    "message": {
                        "message_id": 15,
                        "chat": {"id": int(self.chat_id)},
                        "from": {"id": int(self.chat_id)},
                        "text": "/status"
                    }
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(status_updates).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = self.notifier.poll_approvals([])
        self.assertEqual(res, {"action": "status"})
        # Vérifier que le message sortant contient l'URL du dashboard et la métrique
        sent_call = mock_urlopen.call_args_list[-1]
        sent_payload = json.loads(sent_call[0][0].data.decode("utf-8"))
        self.assertIn("100.90.108.89:8088/dashboard.html", sent_payload["text"])
        self.assertIn("17 / 30", sent_payload["text"])

    @patch("urllib.request.urlopen")
    def test_valid_approval_and_denial_workflow(self, mock_urlopen):
        """Seules les commandes exactes /approve_<nom> et /deny_<nom> sur cible en attente sont traitées."""
        # 1. Test /approve
        approve_updates = {
            "ok": True,
            "result": [
                {
                    "update_id": 3001,
                    "message": {
                        "message_id": 10,
                        "chat": {"id": int(self.chat_id)},
                        "from": {"id": int(self.chat_id)},
                        "text": "/approve_target_gold"
                    }
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(approve_updates).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = self.notifier.poll_approvals(["target_gold"])
        self.assertEqual(res, {"target_name": "target_gold", "action": "approve"})

        # 2. Test /deny
        deny_updates = {
            "ok": True,
            "result": [
                {
                    "update_id": 3002,
                    "message": {
                        "message_id": 11,
                        "chat": {"id": int(self.chat_id)},
                        "from": {"id": int(self.chat_id)},
                        "text": "/deny_target_gold"
                    }
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(deny_updates).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = self.notifier.poll_approvals(["target_gold"])
        self.assertEqual(res, {"target_name": "target_gold", "action": "deny"})

    @patch("urllib.request.urlopen")
    def test_network_fault_tolerance(self, mock_urlopen):
        """En cas de panne réseau ou de Telegram indisponible, le notifier ne lève jamais d'exception."""
        mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

        # Aucun appel ne doit crasher
        ok_msg = self.notifier.send_message("Test message")
        self.assertFalse(ok_msg)

        ok_gate = self.notifier.notify_gate_triggered("TEST", "Details")
        self.assertFalse(ok_gate)

        ok_proof = self.notifier.notify_proof_certified("t1", "mathd", 0.01, 1)
        self.assertFalse(ok_proof)

        poll_res = self.notifier.poll_approvals(["t1"])
        self.assertIsNone(poll_res)

    def test_target_budget_unlocked_model(self):
        """Vérifie que le modèle Target gère fidèlement l'attribut budget_unlocked."""
        t = Target(name="bounty_1", statement="theorem t1 : True := trivial", kind="bounty", value_usd=100.0)
        self.assertFalse(t.budget_unlocked)
        d = t.to_dict()
        self.assertNotIn("budget_unlocked", d)

        # Déblocage
        t.budget_unlocked = True
        d2 = t.to_dict()
        self.assertTrue(d2["budget_unlocked"])

        # Reconstruction depuis dictionnaire
        t_rebuilt = Target.from_dict(d2)
        self.assertTrue(t_rebuilt.budget_unlocked)

if __name__ == "__main__":
    unittest.main()
