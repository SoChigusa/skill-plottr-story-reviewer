# Observed Plottr `.pltr` Format Notes

These notes are based on observed Plottr JSON files and are practical rather than an official schema.

## Common top-level keys

Observed projects may contain keys such as:

- `file`
- `ui`
- `featureFlags`
- `series`
- `books`
- `beats`
- `cards`
- `categories`
- `characters`
- `customAttributes`
- `attributes`
- `lines`
- `notes`
- `places`
- `tags`
- `hierarchyLevels`
- `images`
- `familyTrees`
- `audioClips`

Preserve unknown keys when editing.

## Beats

`beats` has been observed as a mapping keyed by book ID, with a per-book structure containing:
- `index`: beat ID -> beat record;
- `heap`: beat ID -> parent beat ID or null;
- `children`: parent beat ID -> child beat IDs.

Treat `heap` and `children` as two representations of the same hierarchy and audit them for disagreement.

Beat records commonly include:
- `id`
- `bookId`
- `position`
- `title`
- `time`

## Cards

Cards commonly include:
- `id`
- `lineId`
- `beatId`
- `bookId`
- `positionWithinLine`
- `positionInBeat`
- `title`
- `description`
- `tags`
- `characters`
- `places`

Check that referenced line, beat, tag, character, and place IDs exist.

## Rich text

Plottr text fields may use Slate-like JSON arrays with nodes such as:
- `paragraph`
- `bulleted-list`
- `list-item`
- text leaf nodes containing `text` and optional marks such as `bold`.

When editing text, preserve node structure where practical. When generating comparison views, recursively flatten text leaves for readability rather than assuming plain strings.

## IDs and ordering

Preserve IDs whenever possible. New objects should use IDs not already present in the corresponding collection.

Be cautious with:
- duplicate sibling `position` values;
- cards moved to nonexistent beats;
- cards whose `lineId` was removed;
- tags referenced by cards but absent from the tag list;
- beat hierarchy where `heap` and `children` disagree.

## Transient editor focus and Slate selections

Plottr may persist Slate-style editor selections under `ui.timeline.focus`. These paths point into the exact rich-text tree that existed when the editor last had focus. If a proposal rewrites a card description but preserves an old selection path, Plottr can crash when reopening or focusing that card even though the description JSON itself is valid. A representative failure is `Cannot use 'in' operator to search for 'children' in false`.

For generated or revised comparison files:

- treat `ui.timeline.focus` as transient UI state rather than story content;
- clear it before delivery unless the user explicitly asks to preserve editor cursor/focus state;
- validate every revised rich-text tree so every element node has a list-valued `children` and every leaf has string-valued `text`;
- run `scripts/sanitize_plottr.py` after edits and before final structural validation.

Do not attempt to repair a stale selection path by guessing a new cursor location. Clearing transient focus is safer and does not alter story content.

## Validation scope

A successful JSON parse, rich-text audit, stale-focus cleanup, and clean reference audit still do not guarantee that Plottr itself can open and round-trip the file. Report application-level testing separately.
