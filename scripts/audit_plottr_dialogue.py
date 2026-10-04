#!/usr/bin/env python3
"""Inventory source quotations; require a disposition for every missing quotation.

Read-only audit. Candidates include dialogue, quoted thoughts, document text, and
labels. The tool does not decide which wording is expendable or rewrite a file.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

BLOCKS = {"paragraph", "heading-one", "heading-two", "heading-three", "list-item", "block-quote", "code-block"}


def rich_text(value: Any) -> str:
    """Join marked inline leaves without inserting characters into dialogue."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(rich_text(node) for node in value)
    if isinstance(value, dict):
        if "text" in value:
            return value["text"] if isinstance(value["text"], str) else ""
        children = value.get("children", [])
        if not isinstance(children, list):
            return ""
        sep = "\n" if value.get("type") in {"bulleted-list", "numbered-list", "table", "table-row"} else ""
        return sep.join(rich_text(node) for node in children)
    return ""


def quote_spans(text: str) -> list[dict[str, Any]]:
    """Extract balanced outer Japanese quotations, including nested quotes."""
    pairs = {"\u300c": "\u300d", "\u300e": "\u300f"}
    stack: list[str] = []
    start = 0
    result: list[dict[str, Any]] = []
    for i, char in enumerate(text):
        if char in pairs:
            if not stack:
                start = i
            stack.append(pairs[char])
        elif stack and char == stack[-1]:
            stack.pop()
            if not stack:
                result.append({"quote": text[start:i+1], "start": start, "end": i+1})
    return result


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def scene_name(data: dict, card: dict) -> str:
    bid = str(card.get("beatId"))
    books = data.get("beats", {})
    preferred = books.get(str(card.get("bookId")), {})
    if bid in preferred.get("index", {}):
        return str(preferred["index"][bid].get("title", bid))
    found = [v["index"][bid].get("title", bid) for v in books.values()
             if isinstance(v, dict) and bid in v.get("index", {})]
    return str(found[0]) if len(found) == 1 else f"beat:{bid}"


def inventory(data: dict, line: str = "PL-01", cards: set[str] | None = None) -> list[dict]:
    ids = {str(x["id"]) for x in data.get("lines", []) if str(x.get("title", "")).startswith(line)}
    rows = []
    for card in sorted(data.get("cards", []), key=lambda x: str(x.get("id")).zfill(12)):
        if str(card.get("lineId")) not in ids:
            continue
        if cards is not None and str(card.get("id")) not in cards:
            continue
        cid = str(card["id"])
        content = rich_text(card.get("description", []))
        for ordinal, span in enumerate(quote_spans(content), 1):
            rows.append({"qid": f"D-{cid.zfill(3)}-{ordinal:03d}", "card_id": card["id"],
                         "scene": scene_name(data, card), "title": card.get("title", ""),
                         **span,
                         "context": content[max(0, span["start"]-70):min(len(content), span["end"]+70)]})
    return rows


def occurrence_count(text: str, fragment: str) -> int:
    return text.count(fragment)


def audit(source: dict, proposal: dict, *, baseline: dict | None = None,
          decisions: dict | None = None, line: str = "PL-01", cards: set[str] | None = None) -> dict:
    decisions = decisions or {}
    source_rows = inventory(source, line, cards)
    target = {str(x["id"]): rich_text(x.get("description", [])) for x in proposal.get("cards", [])}
    before = {str(x["id"]): rich_text(x.get("description", [])) for x in (baseline or source).get("cards", [])}
    used: Counter = Counter()
    before_used: Counter = Counter()
    results = []
    errors = []
    qids = {x["qid"] for x in source_rows}
    for qid in decisions:
        if qid not in qids:
            errors.append(f"Disposition references unknown quotation: {qid}")
    for row in source_rows:
        decision = decisions.get(row["qid"], {})
        status = decision.get("status")
        reason = decision.get("reason", "")
        cid = str(decision.get("target_card", row["card_id"]))
        exact = row["quote"]
        replacement = decision.get("replacement", exact)
        result = {**row, "target_card": cid, "reason": reason}
        if status in {"held", "non_dialogue"}:
            if not reason.strip():
                errors.append(f"Reason required: {row['qid']}")
            result["status"] = status
        else:
            token = replacement if status == "adapted" else exact
            key = (cid, token)
            available = occurrence_count(target.get(cid, ""), token)
            if available <= used[key]:
                result["status"] = "unresolved"
                errors.append(f"Missing or insufficient occurrences: {row['qid']}")
            else:
                used[key] += 1
                if status in {"adapted", "moved"}:
                    if not reason.strip():
                        errors.append(f"Reason required: {row['qid']}")
                    result["status"] = status
                    if status == "adapted":
                        result["replacement"] = replacement
                elif status not in {None, "restored", "retained"}:
                    result["status"] = "unresolved"
                    errors.append(f"Unknown disposition status: {row['qid']}: {status}")
                else:
                    bkey = (str(row["card_id"]), exact)
                    present = occurrence_count(before.get(bkey[0], ""), exact) > before_used[bkey]
                    result["status"] = "retained" if present else "restored"
                    before_used[bkey] += 1
        results.append(result)
    counts = dict(Counter(r["status"] for r in results))
    return {"candidate_count": len(results), "counts": counts, "errors": errors,
            "unresolved_count": counts.get("unresolved", 0),
            "notes": ["Quotation candidates include document quotations and labels. Classify manually.",
                      "Preserve speaker, register, punctuation, attribution, knowledge, and timing, not only lexical presence.",
                      "Unquoted dialogue and thoughts require a separate manual source pass."],
            "rows": results}


def markdown(report: dict) -> str:
    out = ["# Dialogue preservation audit", "", f"Candidates: {report['candidate_count']}",
           f"Unresolved: {report['unresolved_count']}", "", "## Counts", ""]
    out += [f"- {k}: {v}" for k, v in sorted(report["counts"].items())]
    if report["errors"]:
        out += ["", "## Errors", ""] + ["- " + e for e in report["errors"]]
    out += ["", "## Source quotations and dispositions", ""]
    for r in report["rows"]:
        out += [f"### {r['qid']} | {r['scene']} | {r['status']}", "", r["quote"], ""]
        if "replacement" in r:
            out += ["Replacement: " + r["replacement"], ""]
        if r["reason"]:
            out += [r["reason"], ""]
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="User-authored source, not only the previous generated proposal")
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--baseline", type=Path, help="Previous generated proposal for retained/restored classification")
    parser.add_argument("--decisions", type=Path, help="Manual dispositions keyed by D-card-ordinal")
    parser.add_argument("--line", default="PL-01")
    parser.add_argument("--cards", nargs="+", help="Restrict source card IDs; inspect the full source separately")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    report = audit(load(args.source), load(args.proposal),
                   baseline=load(args.baseline) if args.baseline else None,
                   decisions=load(args.decisions) if args.decisions else None,
                   line=args.line, cards=set(args.cards) if args.cards else None)
    for path, body in [(args.json_out, json.dumps(report, ensure_ascii=False, indent=2)),
                       (args.markdown, markdown(report))]:
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="rows"}, ensure_ascii=False, indent=2))
    raise SystemExit(2 if report["errors"] else 0)

if __name__ == "__main__":
    main()
