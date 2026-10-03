#!/usr/bin/env python3
"""Find author-facing validation in changed Plottr prose; never rewrite text.

Flags are manual-review hints, not proof that a negative sentence is improper.
Read the installed pink-elephant-guard before the semantic writing pass.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PATTERNS = {
    'authorial_constraint': re.compile(
        r'(?:\u3068\u306f\u8003\u3048\u306a\u3044|\u3068\u306f\u66f8\u304b\u306a\u3044|'
        r'\u3068\u306f\u65ad\u5b9a\u3057\u306a\u3044|\u63cf\u304b\u306a\u3044|'
        r'\u8ffd\u52a0\u3057\u306a\u3044|\u751f\u3084\u3055\u306a\u3044|'
        r'\u78ba\u5b9a\u3057\u306a\u3044|\u65ad\u5b9a\u3057\u306a\u3044|'
        r'\u3053\u3068\u306b\u3057\u306a\u3044|\u4e8b\u306b\u3057\u306a\u3044|'
        r'\u540c\u4e00\u8996\u3057\u306a\u3044|\u5473\u65b9\u306b\u306a\u3089\u306a\u3044|'
        r'\u539f\u56e0\u306b\u3057\u306a\u3044|\u4e0d\u8981\u306a\u7b2c\u4e09\u6bb5\u968e)'
    ),
    'defensive_contrast': re.compile(
        r'(?:\u308f\u3051\u3067\u306f\u306a\u3044|\u306e\u3067\u306f\u306a\u3044|'
        r'\u305f\u3081\u3067\u306f\u306a\u304f|\u304b\u3089\u3067\u306f\u306a\u304f|'
        r'\u3067\u306f\u306a\u304f|\u4ee3\u308f\u308a\u306b\u8aac\u660e\u3059\u308b\u306e\u3067\u306f)'
    ),
    'editor_instruction': re.compile(
        r'(?:\u3053\u3053\u3067[^\u3002]{0,30}\u3057\u306a\u3044|'
        r'\u672c\u6587\u306b\u7f6e\u304f\u6d41\u308c|\u4f5c\u8005\u7528Note\u306b\u7f6e\u304f|'
        r'\u500b\u5225\u306e?Scene\u306f\u4f5c\u3089\u306a\u3044)'
    ),
}
QUOTES = re.compile(r'\u300c[^\u300d]*\u300d|\u300e[^\u300f]*\u300f|"[^"\n]*"')


def read_project(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('cards'), list):
        raise ValueError('Expected a Plottr JSON object with a cards list.')
    return data


def paragraphs(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for node in value:
            result.extend(paragraphs(node))
        return result
    if not isinstance(value, dict):
        return []
    if isinstance(value.get('text'), str):
        return [value['text']]
    children = value.get('children', [])
    if value.get('type') in ('paragraph', 'list-item', 'heading-one', 'heading-two'):
        return [''.join(paragraphs(children))]
    return paragraphs(children)


def lint_text(text: str) -> list[str]:
    visible = QUOTES.sub('', text)
    return [code for code, pattern in PATTERNS.items() if pattern.search(visible)]


def audit(project: dict[str, Any], baseline: dict[str, Any] | None = None,
          line_prefix: str = 'PL-01', card_ids: set[str] | None = None) -> dict[str, Any]:
    old = {str(c.get('id')): c for c in (baseline or {}).get('cards', []) if isinstance(c, dict)}
    lines = {str(x.get('id')): x.get('title', '') for x in project.get('lines', []) if isinstance(x, dict)}
    scenes: dict[str, str] = {}
    for book in project.get('beats', {}).values():
        if isinstance(book, dict):
            for key, rec in book.get('index', {}).items():
                if isinstance(rec, dict):
                    scenes[str(key)] = rec.get('title', '')
    checked = 0
    hints: list[dict[str, Any]] = []
    for card in project['cards']:
        if not isinstance(card, dict):
            continue
        cid = str(card.get('id'))
        if card_ids and cid not in card_ids:
            continue
        if line_prefix and not lines.get(str(card.get('lineId')), '').startswith(line_prefix):
            continue
        if baseline is not None and cid in old and card.get('description') == old[cid].get('description'):
            continue
        checked += 1
        old_text = set(paragraphs(old.get(cid, {}).get('description', [])))
        for n, text in enumerate(paragraphs(card.get('description', [])), 1):
            if text in old_text:
                continue
            codes = lint_text(text)
            if codes:
                hints.append({'card_id': cid, 'scene': scenes.get(str(card.get('beatId')), ''),
                              'paragraph': n, 'hints': codes, 'text': text})
    return {'checked_cards': checked, 'hint_count': len(hints),
            'status': 'manual_review_needed' if hints else 'no_pattern_hints',
            'note': 'Heuristic hints only; preserve genuine dialogue, uncertainty, refusal and story facts. No text was changed.',
            'hints': hints}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('proposal', type=Path)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--line-prefix', default='PL-01')
    parser.add_argument('--card-id', action='append')
    parser.add_argument('--json-out', type=Path)
    parser.add_argument('--markdown', type=Path)
    args = parser.parse_args()
    try:
        data = audit(read_project(args.proposal), read_project(args.baseline) if args.baseline else None,
                     args.line_prefix, set(args.card_id) if args.card_id else None)
        rendered = json.dumps(data, ensure_ascii=False, indent=2)
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(rendered + '\n', encoding='utf-8')
        if args.markdown:
            lines = ['# Prose lint - manual review hints', '', data['note'], '',
                     f"Checked cards: {data['checked_cards']}; hints: {data['hint_count']}", '']
            for hint in data['hints']:
                lines.extend([f"## {hint['scene']} / card {hint['card_id']} / paragraph {hint['paragraph']}",
                              ', '.join(hint['hints']), '', hint['text'], ''])
            args.markdown.write_text('\n'.join(lines), encoding='utf-8')
        print(rendered)
        return 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f'Prose lint failed: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
