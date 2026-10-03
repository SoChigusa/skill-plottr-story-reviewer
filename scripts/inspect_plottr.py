#!/usr/bin/env python3
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ids_from_list(items):
    out = []
    for item in items or []:
        if isinstance(item, dict) and 'id' in item:
            out.append(item['id'])
    return out


def duplicates(values):
    c = Counter(values)
    return sorted([x for x, n in c.items() if n > 1], key=lambda x: str(x))


def beat_books(data):
    beats = data.get('beats', {})
    if not isinstance(beats, dict):
        return []
    result = []
    for key, value in beats.items():
        if key == 'allIds' or not isinstance(value, dict):
            continue
        if isinstance(value.get('index'), dict):
            result.append((str(key), value))
    return result


def normalize_id_set(values):
    return {str(x) for x in values}




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


def resolve_slate_path(root, path):
    current = root
    if not isinstance(path, list):
        return False
    try:
        for key in path:
            if isinstance(current, list):
                current = current[key]
            elif isinstance(current, dict):
                children = current.get('children')
                if not isinstance(children, list):
                    return False
                current = children[key]
            else:
                return False
        return isinstance(current, dict)
    except (IndexError, KeyError, TypeError):
        return False


def audit_rich_text_and_focus(data):
    errors = []
    warnings = []
    cards = data.get('cards', [])
    card_map = {}
    if isinstance(cards, list):
        for card in cards:
            if not isinstance(card, dict):
                continue
            cid = card.get('id')
            card_map[str(cid)] = card
            if 'description' in card:
                errors.extend(validate_rich_text(card.get('description'), f'Card {cid} description'))

    notes = data.get('notes', [])
    if isinstance(notes, list):
        for note in notes:
            if isinstance(note, dict) and 'content' in note:
                errors.extend(validate_rich_text(note.get('content'), f'Note {note.get("id")} content'))

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
                    errors.extend(validate_rich_text(attr['value'], f'{collection_name[:-1].title()} {item.get("id")} attribute[{j}] value'))

    focus = data.get('ui', {}).get('timeline', {}).get('focus', []) if isinstance(data.get('ui'), dict) else []
    stale = 0
    if isinstance(focus, list):
        for entry in focus:
            if not isinstance(entry, dict):
                continue
            target = entry.get('path')
            selection = entry.get('selection')
            if not (isinstance(target, list) and len(target) >= 3 and target[0] == 'card' and target[2] == 'description' and isinstance(selection, dict)):
                continue
            card = card_map.get(str(target[1]))
            if card is None:
                stale += 1
                continue
            desc = card.get('description')
            invalid = False
            for endpoint in ('anchor', 'focus'):
                point = selection.get(endpoint)
                path = point.get('path') if isinstance(point, dict) else None
                if path is not None and not resolve_slate_path(desc, path):
                    invalid = True
            if invalid:
                stale += 1
    if stale:
        warnings.append(f'Stale Plottr editor focus: {stale} saved card-description selection(s) no longer resolve. Clear ui.timeline.focus before delivering a revised file; stale Slate paths can crash description editors.')
    return errors, warnings, stale

def audit(data):
    errors = []
    warnings = []
    info = {}

    if not isinstance(data, dict):
        return {'errors': ['Root JSON value is not an object.'], 'warnings': [], 'info': {}}

    rich_errors, focus_warnings, stale_focus_count = audit_rich_text_and_focus(data)
    errors.extend(rich_errors)
    warnings.extend(focus_warnings)
    info['stale_editor_focus_count'] = stale_focus_count

    collections = {
        'cards': data.get('cards', []),
        'lines': data.get('lines', []),
        'characters': data.get('characters', []),
        'places': data.get('places', []),
        'tags': data.get('tags', []),
        'notes': data.get('notes', []),
    }

    id_sets = {}
    for name, items in collections.items():
        if not isinstance(items, list):
            errors.append(f'Top-level {name} is not a list.')
            items = []
        ids = ids_from_list(items)
        dups = duplicates(ids)
        if dups:
            errors.append(f'Duplicate {name} IDs: {dups}')
        id_sets[name] = normalize_id_set(ids)
        info[f'{name}_count'] = len(items)

    all_beat_ids = set()
    beat_count = 0
    for book_key, b in beat_books(data):
        index = b.get('index', {})
        heap = b.get('heap', {})
        children = b.get('children', {})
        beat_ids = normalize_id_set(index.keys())
        all_beat_ids |= beat_ids
        beat_count += len(index)

        for key, rec in index.items():
            sid = str(key)
            if isinstance(rec, dict) and str(rec.get('id')) != sid:
                warnings.append(f'Book {book_key}: beat index key {sid} disagrees with record id {rec.get("id")}.')

        for child, parent in heap.items():
            child = str(child)
            if child not in beat_ids:
                errors.append(f'Book {book_key}: heap references missing child beat {child}.')
            if parent is not None and str(parent) not in beat_ids:
                errors.append(f'Book {book_key}: beat {child} has missing parent {parent}.')

        seen_child_parents = defaultdict(list)
        for parent, kids in children.items():
            if not isinstance(kids, list):
                warnings.append(f'Book {book_key}: children[{parent}] is not a list.')
                continue
            p = None if str(parent) == 'null' else str(parent)
            if p is not None and p not in beat_ids:
                warnings.append(f'Book {book_key}: children map has unknown parent {parent}.')
            for kid in kids:
                k = str(kid)
                seen_child_parents[k].append(p)
                if k not in beat_ids:
                    errors.append(f'Book {book_key}: children[{parent}] references missing beat {k}.')
                heap_parent = heap.get(kid, heap.get(k))
                heap_parent = None if heap_parent is None else str(heap_parent)
                if heap_parent != p:
                    warnings.append(f'Book {book_key}: hierarchy mismatch for beat {k}: heap parent={heap_parent}, children parent={p}.')

        for child, parents in seen_child_parents.items():
            if len(parents) > 1:
                warnings.append(f'Book {book_key}: beat {child} appears under multiple parents: {parents}.')

        siblings = defaultdict(list)
        for key, rec in index.items():
            if not isinstance(rec, dict):
                continue
            parent = heap.get(key, heap.get(int(key)) if str(key).isdigit() else None)
            siblings[str(parent)].append((rec.get('position'), str(key), rec.get('title', '')))
        for parent, rows in siblings.items():
            pos_counts = Counter(r[0] for r in rows if r[0] is not None)
            for pos, n in pos_counts.items():
                if n > 1:
                    examples = [(bid, title) for p, bid, title in rows if p == pos]
                    warnings.append(f'Book {book_key}: duplicate sibling beat position {pos} under parent {parent}: {examples}.')

    info['beat_count'] = beat_count

    line_ids = id_sets['lines']
    tag_ids = id_sets['tags']
    char_ids = id_sets['characters']
    place_ids = id_sets['places']

    card_slots = defaultdict(list)
    for card in data.get('cards', []) if isinstance(data.get('cards', []), list) else []:
        if not isinstance(card, dict):
            warnings.append('Encountered a non-object card.')
            continue
        cid = card.get('id')
        beat_id = card.get('beatId')
        line_id = card.get('lineId')
        if beat_id is not None and str(beat_id) not in all_beat_ids:
            errors.append(f'Card {cid} references missing beatId {beat_id}.')
        if line_id is not None and str(line_id) not in line_ids:
            errors.append(f'Card {cid} references missing lineId {line_id}.')
        for field, valid in [('tags', tag_ids), ('characters', char_ids), ('places', place_ids)]:
            vals = card.get(field, []) or []
            if not isinstance(vals, list):
                warnings.append(f'Card {cid} field {field} is not a list.')
                continue
            for value in vals:
                if str(value) not in valid:
                    errors.append(f'Card {cid} references missing {field[:-1]} ID {value}.')
        slot = (str(beat_id), str(line_id), card.get('positionInBeat'), card.get('positionWithinLine'))
        card_slots[slot].append(cid)

    for slot, ids in card_slots.items():
        if len(ids) > 1 and None not in slot:
            warnings.append(f'Multiple cards share the same beat/line/position slot {slot}: {ids}.')

    line_positions = defaultdict(list)
    for line in data.get('lines', []) if isinstance(data.get('lines', []), list) else []:
        if isinstance(line, dict):
            line_positions[(str(line.get('bookId')), line.get('position'))].append((line.get('id'), line.get('title')))
    for key, rows in line_positions.items():
        if key[1] is not None and len(rows) > 1:
            warnings.append(f'Duplicate line position for book/position {key}: {rows}.')

    return {'errors': errors, 'warnings': warnings, 'info': info}


def to_markdown(source, result):
    lines = [
        '# Plottr structural audit',
        '',
        f'- Source: `{source}`',
        f'- Errors: **{len(result["errors"])}**',
        f'- Warnings: **{len(result["warnings"])}**',
        '',
        '## Counts',
        '',
    ]
    for k, v in sorted(result['info'].items()):
        lines.append(f'- {k}: {v}')
    lines += ['', '## Errors', '']
    if result['errors']:
        lines += [f'- {x}' for x in result['errors']]
    else:
        lines.append('- None detected.')
    lines += ['', '## Warnings', '']
    if result['warnings']:
        lines += [f'- {x}' for x in result['warnings']]
    else:
        lines.append('- None detected.')
    lines += ['', '## Scope', '', 'This audit checks JSON structure, rich-text node validity, common reference relationships, and stale saved card-description selections. It does not prove that Plottr itself can open and round-trip the file, and it does not judge story quality.']
    return '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser(description='Audit common structural relationships in a Plottr .pltr JSON file.')
    ap.add_argument('source')
    ap.add_argument('--markdown')
    ap.add_argument('--json-out')
    args = ap.parse_args()

    try:
        data = load_json(args.source)
    except Exception as exc:
        result = {'errors': [f'Failed to parse JSON: {exc}'], 'warnings': [], 'info': {}}
        if args.markdown:
            Path(args.markdown).write_text(to_markdown(args.source, result), encoding='utf-8')
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    result = audit(data)
    if args.markdown:
        Path(args.markdown).write_text(to_markdown(args.source, result), encoding='utf-8')
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result['errors'] else 0)


if __name__ == '__main__':
    main()
