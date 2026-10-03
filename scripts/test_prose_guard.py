#!/usr/bin/env python3
"""Regression checks for prose hints and non-destructive sanitization."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from lint_plottr_prose import audit, lint_text

ROOT = Path(__file__).resolve().parent


def paragraph(text):
    return {'type': 'paragraph', 'children': [{'text': text}]}


class ProseGuardTests(unittest.TestCase):
    def test_positive_action(self):
        self.assertEqual(lint_text('\u4e3b\u4eba\u516c\u306f\u5c11\u5973\u306e\u8fd4\u4e8b\u3092\u5f85\u3064\u3002'), [])

    def test_rejected_hypothesis(self):
        self.assertIn('authorial_constraint', lint_text('\u76e3\u67fb\u3060\u3051\u3067\u5165\u308c\u308b\u3068\u306f\u8003\u3048\u306a\u3044\u3002'))

    def test_new_power_comment(self):
        self.assertIn('authorial_constraint', lint_text('\u65b0\u3057\u3044\u80fd\u529b\u3092\u8ffd\u52a0\u3057\u306a\u3044\u3002'))

    def test_guard_comment(self):
        self.assertIn('authorial_constraint', lint_text('\u770b\u5b88\u306f\u5473\u65b9\u306b\u306a\u3089\u306a\u3044\u3002'))

    def test_actual_refusal_is_not_flagged(self):
        self.assertEqual(lint_text('\u5f7c\u306f\u300c\u79c1\u306f\u8f9e\u3081\u3066\u3044\u306a\u3044\u300d\u3068\u8a00\u3046\u3002'), [])

    def test_character_instruction_is_not_flagged(self):
        self.assertEqual(lint_text('\u5c11\u5973\u306f\u300c\u307e\u3060\u958b\u3051\u306a\u3044\u3067\u300d\u3068\u8a00\u3046\u3002'), [])

    def test_uncertainty_is_preserved(self):
        self.assertEqual(lint_text('\u5c11\u5973\u304b\u3089\u8fd4\u4e8b\u306f\u306a\u3044\u3002\u751f\u5b58\u306f\u78ba\u8a8d\u4e2d\u3060\u3002'), [])

    def test_quote_can_include_contrast(self):
        self.assertEqual(lint_text('\u300c\u4ee3\u8868\u3067\u306f\u306a\u304f\u3001\u79c1\u306e\u8a71\u3060\u300d'), [])

    def fixture(self):
        text = '\u65b0\u3057\u3044\u80fd\u529b\u3092\u8ffd\u52a0\u3057\u306a\u3044\u3002'
        return {'cards': [{'id': 1, 'lineId': 2, 'beatId': 3, 'description': [paragraph(text)]}],
                'lines': [{'id': 2, 'title': 'PL-01'}],
                'beats': {'1': {'index': {'3': {'title': 'E07-S06'}}}}}

    def test_baseline_skips_unchanged_card(self):
        d = self.fixture()
        self.assertEqual(audit(d, copy.deepcopy(d))['checked_cards'], 0)

    def test_unchanged_paragraph_not_reflagged(self):
        before = self.fixture()
        after = copy.deepcopy(before)
        after['cards'][0]['description'].append(paragraph('New action.'))
        result = audit(after, before)
        self.assertEqual(result['checked_cards'], 1)
        self.assertEqual(result['hint_count'], 0)

    def test_other_plotline_excluded(self):
        d = self.fixture()
        d['lines'][0]['title'] = 'PL-05'
        self.assertEqual(audit(d)['checked_cards'], 0)

    def test_read_only(self):
        d = self.fixture()
        snapshot = copy.deepcopy(d)
        self.assertEqual(audit(d)['hint_count'], 1)
        self.assertEqual(d, snapshot)

    def test_sanitizer_preserves_metadata(self):
        data = {'cards': [{'id': 1, 'description': [paragraph('x')]}], 'notes': [],
                'ui': {'timeline': {'focus': [{'old': True}], 'zoom': 3}},
                'file': {'fileName': 'Keep this', 'dirty': True, 'loaded': False},
                'unknown': {'retain': 1}}
        with tempfile.TemporaryDirectory() as temp:
            src, dst = Path(temp)/'source.pltr', Path(temp)/'proposal.pltr'
            src.write_text(json.dumps(data), encoding='utf-8')
            subprocess.run([sys.executable, str(ROOT/'sanitize_plottr.py'), str(src), str(dst)],
                           check=True, capture_output=True, text=True)
            actual = json.loads(dst.read_text())
            expected = copy.deepcopy(data)
            expected['ui']['timeline']['focus'] = []
            self.assertEqual(actual, expected)
            self.assertEqual(json.loads(src.read_text()), data)


if __name__ == '__main__':
    unittest.main()
