# Output Contract

## Review package contents

When a review package is useful, prefer these outputs:

- `*_proposal.pltr` — comparison copy with proposed edits only.
- `comparison.html` — side-by-side or before/after comparison.
- `review.md` — detailed review in a durable text format.
- `review.html` — optional readable rendered review.
- `validation.md` or `validation.json` — structural audit result.
- `manifest.txt` — optional list of packaged files and status notes.

### Original-file rule

Do **not** include the user's original `.pltr` in the review ZIP by default. Assume the user retains their original independently.

Include it only when the user explicitly asks for an archival bundle containing the source.


## Minimal-change rule

For a targeted review such as `E07`, the proposal file should change `E07` and only the specific external dependencies required by those changes. Reading or checking other Episodes does not authorize editing them.

- Do not rewrite unaffected Scenes, Notes, characters, Plotlines, or foreshadowing rows.
- In shared ledgers, modify only the affected `F##` rows/cells.
- Never write `既存内容を維持`, `変更なし`, `現状維持`, or similar no-op text into the proposal. Unchanged means unchanged.
- Keep unapproved `R-###` entries in the review document rather than adding them to the Plottr revision-history Note by default.
- Before delivery, inspect all changed objects and revert any item that cannot be justified as either the named target or a necessary dependency.

## Proposal-file status

A proposal `.pltr` is not canon.
- Preserve the original externally.
- If revision-history entries are explicitly requested before approval, label them as proposed. Otherwise keep unapproved revision IDs in the review report only.
- Do not imply that opening or downloading the proposal adopts it.

## Comparison HTML

Make comparison pages useful for actual editing:
- show object IDs and titles;
- group by beats/Scenes/cards/Notes/characters;
- show only changed objects by default;
- preserve Japanese text correctly;
- support browser text search for IDs such as `E07-S06`, `F12`, or `R-319`;
- include a summary of added/removed/modified objects.

## Review prose

Start with a short overall judgment and what should be preserved.
Then discuss the highest-impact issues in prose before the complete proposal table.

Do not use the table as a substitute for explaining the central structural problem.

## Validation language

Distinguish:
- JSON/schema/reference checks performed by script;
- semantic/story checks performed by analysis;
- Plottr application round-trip checks.

If Plottr itself was not available to open and resave the file, state that explicitly.

## Execution-facing prose

Load the installed `pink-elephant-guard` before drafting descriptions when available; see `SKILL.md` and `prose-style.md`. Write character motives and actions directly, in the source's register. Separate scene prose from diagnostic validation. Keep before/after reasoning in the report, and keep rejected hypothetical actions out of the story description unless a character genuinely considers or refuses them.

For a PL-01-only wording revision, preserve every other field and object. Preserve unchanged PL-01 paragraphs as well. Output the actual replacement passages with Scene/card IDs, a changed-only comparison, and optionally the full proposal file with only those replacements. Do not append editor commentary to Notes or refill ledgers to explain a prose edit.

For missing dependencies, distinguish an instruction to load a skill in future local use from actually having read or installed it in this session.
