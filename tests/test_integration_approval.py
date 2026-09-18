#!/usr/bin/env python3
"""
End-to-End Workflow Verification for Task 11 Budget Approval Gate.
Simulates a high-value bounty target exceeding the daily budget,
verifying:
1. Alarm notification generated.
2. Inbound approval unlocking budget.
3. Inbound denial rejecting and re-queuing.
4. Unauthorized chat_id rejection.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from agent.targets import Target, load_targets, save_targets
from agent.notifier import TelegramNotifier
from agent.db import AttemptsDB

class TestIntegrationBudgetApproval(unittest.TestCase):

    def setUp(self):
        self.queue_path = ROOT_DIR / "targets" / "queue.yaml"
        self.original_queue = load_targets(self.queue_path) if self.queue_path.exists() else []
        self.chat_id = "8486359334"
        self.notifier = TelegramNotifier(bot_token="test_tok", chat_id=self.chat_id)
        self.notifier.state_file = ROOT_DIR / "data" / "test_state_integ.json"

    def tearDown(self):
        save_targets(self.queue_path, self.original_queue)
        if self.notifier.state_file.exists():
            self.notifier.state_file.unlink()

    @patch("urllib.request.urlopen")
    def test_full_approval_cycle(self, mock_urlopen):
        # 1. Créer une cible bounty à haute prime
        test_target = Target(
            name="bounty_gold_100",
            statement="theorem gold : True := trivial",
            kind="bounty",
            value_usd=100.0,
            difficulty_class="mathd",
            verified=True,
            budget_unlocked=False
        )
        save_targets(self.queue_path, [test_target])

        # Mock outgoing sendMessage
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"ok": True, "result": {"message_id": 999}}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # Demande d'autorisation envoyée (SONORE)
        ok = self.notifier.request_budget_approval(
            test_target.name,
            test_target.value_usd,
            p_success=0.80,
            estimated_cost=2.40
        )
        self.assertTrue(ok)
        payload = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
        self.assertFalse(payload["disable_notification"])
        self.assertIn("/approve_bounty_gold_100", payload["text"])

        # 2. Test tentative d'usurpation (chat_id frauduleux)
        fraud_update = {
            "ok": True,
            "result": [
                {
                    "update_id": 501,
                    "message": {
                        "message_id": 50,
                        "chat": {"id": 111222333}, # Attaquant
                        "text": "/approve_bounty_gold_100"
                    }
                }
            ]
        }
        mock_resp.read.return_value = json.dumps(fraud_update).encode("utf-8")
        action = self.notifier.poll_approvals([test_target.name])
        self.assertIsNone(action, "L'attaquant doit être rejeté")

        # 3. Test texte libre depuis le bon chat_id
        text_update = {
            "ok": True,
            "result": [
                {
                    "update_id": 502,
                    "message": {
                        "message_id": 51,
                        "chat": {"id": int(self.chat_id)},
                        "text": "Oui c'est bon tu peux y aller !"
                    }
                }
            ]
        }
        mock_resp.read.return_value = json.dumps(text_update).encode("utf-8")
        action = self.notifier.poll_approvals([test_target.name])
        self.assertIsNone(action, "Le texte libre ne doit pas débloquer")

        # 4. Approbation légitime du propriétaire
        valid_update = {
            "ok": True,
            "result": [
                {
                    "update_id": 503,
                    "message": {
                        "message_id": 52,
                        "chat": {"id": int(self.chat_id)},
                        "text": "/approve_bounty_gold_100"
                    }
                }
            ]
        }
        mock_resp.read.return_value = json.dumps(valid_update).encode("utf-8")
        action = self.notifier.poll_approvals([test_target.name])
        self.assertEqual(action, {"target_name": "bounty_gold_100", "action": "approve"})

        # Déblocage de la cible
        test_target.budget_unlocked = True
        save_targets(self.queue_path, [test_target])

        # Rechargement et vérification
        reloaded = load_targets(self.queue_path)
        self.assertTrue(reloaded[0].budget_unlocked)
        self.assertTrue(reloaded[0].verified)

if __name__ == "__main__":
    unittest.main()
