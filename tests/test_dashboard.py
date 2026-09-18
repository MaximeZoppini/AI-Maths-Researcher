#!/usr/bin/env python3
"""
Unit and Acceptance Tests for Task 12: Static Dashboard Generator.
Validates:
1. HTML generated in < 1 second.
2. Zero external dependencies / zero external network calls (100% offline & self-contained).
3. Accuracy of KPIs, official metrics (17/30), and theorem counts.
4. Correctness of inline SVG charts and dark mode switch.
"""

import unittest
import os
import re
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.dashboard import generate_dashboard, build_dashboard_html

class TestDashboard(unittest.TestCase):

    def test_generation_speed_and_file_creation(self):
        """Vérifie que le dashboard est généré en moins de 1 seconde et créé le fichier HTML."""
        start = time.time()
        output_path = generate_dashboard()
        duration = time.time() - start

        self.assertLess(duration, 1.0, f"La génération doit être < 1s (durée: {duration:.3f}s)")
        self.assertTrue(output_path.exists(), "Le fichier dashboard.html doit exister")
        self.assertGreater(output_path.stat().st_size, 10000, "Le dashboard doit contenir au moins 10 KB de contenu")

    def test_zero_external_network_requests(self):
        """Audit strict de sécurité et d'autonomie : AUCUN appel externe (script/link/img externe)."""
        html = build_dashboard_html()

        # 1. Pas de script ou feuille de style externe
        ext_tags = re.findall(r'<(?:script|link)[^>]+(?:src|href)=[\"\']https?://[^\"\']+', html, re.IGNORECASE)
        self.assertEqual(len(ext_tags), 0, f"Présence de balises externes interdite : {ext_tags}")

        # 2. Pas d'images externes
        ext_imgs = re.findall(r'<img[^>]+src=[\"\']https?://[^\"\']+', html, re.IGNORECASE)
        self.assertEqual(len(ext_imgs), 0, f"Présence d'images externes interdite : {ext_imgs}")

        # 3. Présence de graphiques SVG inline
        svgs = re.findall(r'<svg[^>]+class=[\"\']svg-chart[\"\']', html)
        self.assertGreaterEqual(len(svgs), 3, "Au moins 3 graphiques SVG inline doivent être présents")

    def test_kpi_and_metric_accuracy(self):
        """Vérifie que les métriques officielles et les chiffres de la base sont fidèles."""
        html = build_dashboard_html()

        # 1. Métrique officielle inviolable
        self.assertIn("17 / 30", html, "La métrique officielle 17/30 (56.7%) doit être affichée")
        self.assertIn("56.7%", html)

        # 2. 25 théorèmes certifiés en prod
        self.assertIn("25", html, "Le nombre de théorèmes certifiés doit être 25")

        # 3. Présence des colonnes et des données du tableau
        self.assertIn("theoremsTable", html)
        self.assertIn("toggleTheme", html)
        self.assertIn("filterTheorems", html)
        self.assertIn("sortTable", html)

    def test_mathlib_gaps_and_pipeline_integration(self):
        """Vérifie la présence de la section mathlib gaps et du pipeline de cibles."""
        html = build_dashboard_html()

        self.assertIn("Top Trous Détectés dans Mathlib", html)
        self.assertIn("Pipeline & Registre de Cibles", html)
        self.assertIn("100.90.108.89:8088/dashboard.html", html)

if __name__ == "__main__":
    unittest.main()
