#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))


def validate_rich_text(value, label):
    errors = []
    if not isinstance(value, list):
        return [f'{label}: rich-text root must be a list, got {type(value).__name__}.']

    def walk(node, path):
        if not isinstance(node, dict):
            errors.append(f'{path}: rich-text node must be an object, got {type(node).__name__}.')
            return
        if 'text' in node:
            if not isinstance(node.get('text'), str):
                errors.append(f'{path}.text: expected string, got {type(node.get("text")).__name__}.')
            if 'children' in node:
                errors.append(f'{path}: text leaf unexpectedly contains children.')
            return
        children = node.get('children')
        if not isinstance(children, list):
            errors.append(f'{path}.children: expected list, got {type(children).__name__}.')
            return
        for i, child in enumerate(children):
            walk(child, f'{path}.children[{i}]')

    for i, node in enumerate(value):
        walk(node, f'{label}[{i}]')
    return errors


def audit_rich_text(data):
    errors = []
    cards = data.get('cards', [])
    if isinstance(cards, list):
        for card in cards:
            if isinstance(card, dict) and 'description' in card:
                errors.extend(validate_rich_text(card.get('description'), f'card {card.get("id")} description'))

    notes = data.get('notes', [])
    if isinstance(notes, list):
        for note in notes:
            if isinstance(note, dict) and 'content' in note:
                errors.extend(validate_rich_text(note.get('content'), f'note {note.get("id")} content'))

    for collection_name in ('characters', 'places'):
        items = data.get(collection_name, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            attrs = item.get('attributes', [])
            if not isinstance(attrs, list):
                continue
            for j, attr in enumerate(attrs):
                if isinstance(attr, dict) and isinstance(attr.get('value'), list):
                    errors.extend(validate_rich_text(attr['value'], f'{collection_name[:-1]} {item.get("id")} attribute[{j}] value'))
    return errors


def main():
    ap = argparse.ArgumentParser(description='Prepare a revised Plottr file for delivery by removing stale transient editor focus and validating rich-text trees.')
    ap.add_argument('source')
    ap.add_argument('output')
    ap.add_argument('--preserve-editor-focus', action='store_true', help='Keep ui.timeline.focus. Normally unsafe after rich-text edits.')
    ap.add_argument('--update-file-metadata', action='store_true', help='Explicitly update fileName/dirty/loaded; preserve them by default for minimal diffs.')
    args = ap.parse_args()

    data = load(args.source)
    errors = audit_rich_text(data)
    if errors:
        print(json.dumps({'errors': errors}, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    cleared = 0
    if not args.preserve_editor_focus:
        ui = data.get('ui')
        if isinstance(ui, dict):
            timeline = ui.get('timeline')
            if isinstance(timeline, dict) and isinstance(timeline.get('focus'), list):
                cleared = len(timeline['focus'])
                timeline['focus'] = []

    file_meta = data.get('file')
    if args.update_file_metadata and isinstance(file_meta, dict):
        file_meta['dirty'] = False
        file_meta['loaded'] = True
        file_meta['fileName'] = Path(args.output).stem

    save(args.output, data)
    print(json.dumps({'output': args.output, 'cleared_editor_focus_entries': cleared, 'rich_text_errors': 0}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
