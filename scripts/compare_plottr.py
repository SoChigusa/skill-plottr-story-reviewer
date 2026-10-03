#!/usr/bin/env python3
import argparse
import difflib
import html
import json
from pathlib import Path


def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def flatten_text(value):
    out = []
    def walk(x):
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, list):
            for y in x:
                walk(y)
                if isinstance(y, dict) and y.get('type') in {'paragraph', 'list-item'}:
                    out.append('\n')
        elif isinstance(x, dict):
            if isinstance(x.get('text'), str):
                out.append(x['text'])
            else:
                for k, v in x.items():
                    if k not in {'id', 'bookId', 'categoryId', 'imageId', 'audioClipId'}:
                        walk(v)
    walk(value)
    return ''.join(out).strip()


def by_id(items):
    return {str(x.get('id')): x for x in items or [] if isinstance(x, dict) and 'id' in x}


def beat_map(data):
    out = {}
    beats = data.get('beats', {})
    if not isinstance(beats, dict):
        return out
    for book_key, b in beats.items():
        if not isinstance(b, dict) or not isinstance(b.get('index'), dict):
            continue
        heap = b.get('heap', {})
        index = b['index']
        for key, rec in index.items():
            if not isinstance(rec, dict):
                continue
            out[str(key)] = {'book': str(book_key), 'record': rec, 'parent': heap.get(key, heap.get(int(key)) if str(key).isdigit() else None)}
    return out


def changed_ids(a, b):
    keys = sorted(set(a) | set(b), key=lambda x: (not str(x).isdigit(), int(x) if str(x).isdigit() else str(x)))
    return [k for k in keys if a.get(k) != b.get(k)]


def esc(x):
    return html.escape('' if x is None else str(x))


def text_diff(a, b):
    a_lines = (a or '').splitlines() or ['']
    b_lines = (b or '').splitlines() or ['']
    return difflib.HtmlDiff(wrapcolumn=90).make_table(a_lines, b_lines, fromdesc='Original', todesc='Proposal', context=True, numlines=2)


def section(title, body):
    return f'<section><h2>{esc(title)}</h2>{body}</section>'


def compare_collection(title, amap, bmap, render):
    ids = changed_ids(amap, bmap)
    if not ids:
        return ''
    parts = [f'<p>{len(ids)} changed object(s).</p>']
    for oid in ids:
        a = amap.get(oid)
        b = bmap.get(oid)
        status = 'modified' if a is not None and b is not None else ('added' if a is None else 'removed')
        label = ''
        src = b if b is not None else a
        if isinstance(src, dict):
            label = src.get('title') or src.get('name') or ''
        parts.append(f'<details open id="obj-{esc(oid)}"><summary><strong>{esc(oid)}</strong> {esc(label)} <em>({status})</em></summary>{render(a,b)}</details>')
    return section(title, ''.join(parts))


def render_generic(a, b, fields):
    rows = ['<table class="kv"><tr><th>Field</th><th>Original</th><th>Proposal</th></tr>']
    for field in fields:
        av = '' if a is None else a.get(field)
        bv = '' if b is None else b.get(field)
        if field in {'description', 'content', 'notes', 'attributes'}:
            av = flatten_text(av)
            bv = flatten_text(bv)
        if av == bv:
            continue
        rows.append(f'<tr><td>{esc(field)}</td><td><pre>{esc(av)}</pre></td><td><pre>{esc(bv)}</pre></td></tr>')
    rows.append('</table>')
    at = flatten_text(a.get('description') if isinstance(a,dict) else '')
    bt = flatten_text(b.get('description') if isinstance(b,dict) else '')
    if at != bt and (at or bt):
        rows.append(text_diff(at, bt))
    return ''.join(rows)


def main():
    ap = argparse.ArgumentParser(description='Generate a readable HTML comparison for two Plottr files.')
    ap.add_argument('original')
    ap.add_argument('proposal')
    ap.add_argument('output')
    args = ap.parse_args()

    a = load(args.original)
    b = load(args.proposal)

    a_beats = beat_map(a)
    b_beats = beat_map(b)
    a_cards, b_cards = by_id(a.get('cards')), by_id(b.get('cards'))
    a_notes, b_notes = by_id(a.get('notes')), by_id(b.get('notes'))
    a_chars, b_chars = by_id(a.get('characters')), by_id(b.get('characters'))
    a_lines, b_lines = by_id(a.get('lines')), by_id(b.get('lines'))

    summary = {
        'beats': len(changed_ids(a_beats,b_beats)),
        'cards': len(changed_ids(a_cards,b_cards)),
        'notes': len(changed_ids(a_notes,b_notes)),
        'characters': len(changed_ids(a_chars,b_chars)),
        'lines': len(changed_ids(a_lines,b_lines)),
    }

    css = '''
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;max-width:1400px;margin:32px auto;padding:0 24px;line-height:1.5;color:#222}
    h1,h2{line-height:1.2} section{margin:36px 0} details{border:1px solid #ddd;border-radius:8px;padding:10px 14px;margin:12px 0} summary{cursor:pointer}
    table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px} th,td{border:1px solid #ddd;padding:8px;vertical-align:top} th{background:#f6f6f6} pre{white-space:pre-wrap;margin:0}
    .stats{display:flex;gap:12px;flex-wrap:wrap}.stat{border:1px solid #ddd;border-radius:8px;padding:10px 14px}.diff_header{background:#eee}.diff_add{background:#eaffea}.diff_sub{background:#ffecec}.diff_chg{background:#fff6cc}
    '''

    beat_fields = ['book','parent','record']
    html_parts = [
        '<!doctype html><html><head><meta charset="utf-8"><title>Plottr comparison</title><style>'+css+'</style></head><body>',
        '<h1>Plottr comparison</h1>',
        f'<p><strong>Original:</strong> {esc(args.original)}<br><strong>Proposal:</strong> {esc(args.proposal)}</p>',
        '<div class="stats">' + ''.join(f'<div class="stat"><strong>{esc(k)}</strong>: {v}</div>' for k,v in summary.items()) + '</div>',
    ]

    html_parts.append(compare_collection('Beats / hierarchy', a_beats, b_beats, lambda x,y: render_generic(x,y,beat_fields)))
    html_parts.append(compare_collection('Cards', a_cards, b_cards, lambda x,y: render_generic(x,y,['title','beatId','lineId','positionInBeat','positionWithinLine','description','tags','characters','places'])))
    html_parts.append(compare_collection('Notes', a_notes, b_notes, lambda x,y: render_generic(x,y,['title','content','tags','characters','places','position'])))
    html_parts.append(compare_collection('Characters', a_chars, b_chars, lambda x,y: render_generic(x,y,['name','description','notes','attributes','tags'])))
    html_parts.append(compare_collection('Plotlines / lines', a_lines, b_lines, lambda x,y: render_generic(x,y,['title','bookId','position','characterId'])))
    html_parts.append('<p><em>This comparison is a JSON-level aid and is not a Plottr application round-trip test.</em></p></body></html>')

    Path(args.output).write_text(''.join(html_parts), encoding='utf-8')
    print(args.output)


if __name__ == '__main__':
    main()
