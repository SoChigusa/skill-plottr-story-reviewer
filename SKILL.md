---
name: plottr-story-reviewer
description: Review and improve Plottr story projects, especially `.pltr` files, with cross-episode structural analysis, causality and timeline checks, character-arc and POV checks, foreshadowing-ledger review, theme progression, information-state tracking, and Plottr file-integrity validation. Use when a user asks to review, diagnose, compare, revise, or improve a Plottr project or plot/story structure, or asks for a revised comparison `.pltr` plus review artifacts. Preserve canon vs proposals, use fixed revision IDs, read broadly but edit only the named target and necessary dependencies, and never include the user's original `.pltr` inside a review ZIP unless explicitly requested.
---

# Plottr Story Reviewer

Review a Plottr project as both a story system and a structured file. Preserve what already works, identify causal and thematic weak points, and produce concrete revision proposals without silently promoting them to canon.

## Writing pass: load the prose guard

Before drafting or rewriting Plottr descriptions, look up the installed `pink-elephant-guard` skill by its exact name and read its entrypoint. Use the skill resource interface when available. In a local filesystem-enabled session, also check the existing `~/.agents/skills/pink-elephant-guard/SKILL.md` (or `skill.md`). Reuse that skill in place; do not embed, recreate, or maintain a second copy here.

If the entrypoint is inaccessible, state that briefly, apply the user's explicit prose requirements below, and mark the dependency as not read. Do not imply that the guard was applied or infer its full contents from its name. Read `references/prose-style.md` for this reviewer's own writing rules and examples; these are user-requested rules, not a substitute copy of the missing guard.

Write PL-01 and other execution-facing descriptions as concise scene outlines: **what the character notices, wants, chooses, and does; what changes next**. Keep the source's emotional register and meaningful dialogue. Put diagnostic reasoning and comparisons of rejected options in the review report.

Before delivery, reread every changed prose passage aloud in sequence. Replace author-facing defensive validation with the actual positive motive or action. Preserve genuine refusals, factual absences, uncertainty, danger, and character hesitation when these belong to the story. Use `scripts/lint_plottr_prose.py <proposal.pltr> --baseline <source.pltr> --json-out <prose-lint.json>` to locate candidates for manual review; the tool never rewrites text and its flags are not factual verdicts.

For wording-only requests, lock events, evidence, chronology, knowledge limits, viewpoint, character relationships, scene count, titles, and IDs. Rephrase only the requested changed descriptions. Preserve untouched paragraphs and rich-text nodes exactly. Report any substantive contradiction separately rather than repairing plot during a style pass.

## Core workflow

1. **Preserve the source.**
   - Treat the supplied `.pltr` as the user's source of truth for this review pass.
   - Never overwrite it unless the user explicitly asks.
   - If producing a review bundle, do **not** include the original `.pltr` in the ZIP unless the user explicitly requests that.

2. **Read broadly, edit narrowly.**
   - For an Episode review, inspect at minimum the target Episode, adjacent Episodes, relevant Plotlines, character records, Notes, foreshadowing entries, theme state, and information-state records.
   - Reading a scene, Episode, Note, character record, or foreshadowing row does **not** make it part of the edit scope.
   - If the user asks to review `E07`, default the write scope to `E07` only. Expand the write scope outside `E07` only when a concrete E07 proposal requires a specific earlier setup, later payoff, shared character/world fact, or foreshadowing entry to change.
   - Follow dependencies as far as needed for analysis, but modify only the smallest directly affected set of objects.
   - Do not critique an intentionally blank or unfinished Episode as if it were final; instead identify what must be seeded there for later material to work. If a seed is only a recommendation and is not needed in the comparison file yet, keep it in the review report instead of editing that earlier Episode.

3. **Run a structural audit before or alongside story analysis.**
   - Run `scripts/inspect_plottr.py <file.pltr> --markdown <audit.md>` when code execution is available.
   - Use its findings for JSON validity, duplicate IDs, dangling card references, beat hierarchy inconsistencies, invalid tag/character/place/line references, and suspicious ordering.
   - Treat parser findings as structural evidence, not as story conclusions.

4. **Review in this order.**
   - What should be preserved.
   - Major causality, time-order, and information-state problems.
   - Episode-to-Episode causality and irreversible differences.
   - Character arcs, motives, relationships, and agency.
   - POV and who knows what when.
   - Foreshadowing interactions and payoff fairness.
   - Theme progression and climax behavior.
   - Setting, ability, language, logistics, and world-rule contradictions.
   - Plottr/file-structure problems.
   - Optional compression, pacing, and presentation improvements.

5. **Use counterfactual tests on major beats.**
   - Ask: “If this character/action were removed, would the same outcome still happen?”
   - Ask: “Does an event in Scene N depend on information or success that only occurs in Scene N+1?”
   - Ask: “Could the antagonist achieve the same goal more safely or simply?”
   - Ask: “Does the climax solve the external problem through the theme, or merely happen beside the theme?”
   - Ask: “Would the payoff still work if the reader remembered only the earlier planted information?”

6. **Distinguish three statuses throughout.**
   - Confirmed/canonical project facts.
   - User-stated but still provisional ideas.
   - AI revision proposals.
   Never convert a proposal into canon without user approval.


## Scope discipline for proposal files

Apply this rule strictly: **read broadly, edit narrowly**. A proposal `.pltr` is not a rewritten project; it is a minimal patch expressed as a complete file.

When the user names a target such as `E07`:
- Treat `E07` cards, descriptions, attributes, and directly owned Episode material as the default write scope.
- Change an earlier/later Scene only if the target revision would otherwise be unsupported, contradictory, or impossible. Be able to state the exact dependency.
- Change a shared foreshadowing ledger only for the specific `F##` entries whose seed/strengthening/reveal/payoff actually changes because of the target revision.
- Change a character/world/Note record only if the target revision changes a canonical fact stored there, not merely because that record was consulted.
- Leave every unaffected object and unaffected field unchanged. Do not normalize, restate, summarize, or “refresh” unrelated content.
- In a shared rich-text Note or table, preserve unaffected rows/cells exactly in content and order; surgically edit only the affected rows/cells.

**Never encode non-changes as edits.** Do not insert phrases such as `既存内容を維持`, `変更なし`, `現状維持`, `従来どおり`, or equivalent filler into Plottr merely to show that something was checked. If content is unchanged, leave it unchanged. Preservation can be mentioned in the review prose, not written into the `.pltr`.

Keep revision proposals in the review report by default. Do **not** write every `R-###` proposal into the Plottr revision-history Note before approval; that creates review noise. Update in-project revision history only when the user asks for it or after the corresponding change is approved.

Before delivery, compare original vs proposal and inspect the complete changed-object list. For every changed object outside the named target, verify that it is a necessary dependency. Revert incidental, formatting-only, normalization-only, and no-op changes.

## Story-review lenses

### Causality and chronology

Check every important Scene transition for:
- cause before effect;
- clear state change;
- a reason the next Scene is now necessary;
- no future outcome being used as a prior motive;
- no “waiting for the plot” when a character could act immediately;
- no coincidence replacing an already available causal link.

For each Episode boundary, verify:
- the previous Episode's result causes or constrains the next;
- the Episode has a local question and local answer;
- the Episode leaves an irreversible difference;
- unresolved material is intentional rather than forgotten.

### Character and agency

For each major character, track:
- what they want;
- what they believe;
- what they know;
- what they can actually do;
- what they choose;
- what changes because of that choice.

Do not let supporting characters become mere tools. When several characters contribute to a climax, give each a distinct causal function rather than redundant competence.

Use the counterfactual test aggressively: if the protagonist or a companion can be removed with no change to the outcome, strengthen the causal contribution instead of merely adding more action.

### POV and information state

Track reader knowledge separately from character knowledge.

Flag:
- a POV character withholding a fact from their own internal narration only to preserve a later reveal;
- a character acting on information they have not received;
- exposition that gives a character expertise they have not earned;
- a reveal that repeats information the reader already knows without changing its meaning.

Prefer staged knowledge such as:
1. suspicious fragment;
2. plausible inference;
3. partial confirmation;
4. decisive first-hand fact;
5. reinterpretation/payoff.

### Foreshadowing

Use the project's existing foreshadowing IDs when possible. For any new foreshadowing proposal, specify:
- seed;
- strengthening;
- optional misdirection;
- partial reveal;
- payoff;
- post-payoff meaning.

Do not add a payoff without checking where the seed can fairly appear. Do not overload the Episode immediately before the climax with all necessary setup.

### Theme

Treat theme as a value judgment proven by choice and consequence, not as an explanatory speech.

For a climax, verify:
- the protagonist faces a problem their old method cannot solve;
- they choose the final thematic answer;
- that choice changes behavior;
- the changed behavior materially helps resolve the external problem;
- the resolution does not secretly reproduce the antagonist's value system.

If the bundled canonical template applies, follow its act-function rules in `references/canonical-template.md`.

### World rules and abilities

Separate:
- what the rule says;
- what characters believe the rule says;
- what readers have been shown;
- what the climax requires.

Avoid solving thematic problems through a last-minute power increase unless that is the intended story. Prefer changes in listening conditions, social coordination, information access, or character choice when the theme concerns weak or ignored voices.

### Language and coined terms

Do not present an invented Japanese term as if it were an established term.
- If coining a term, label it as a coinage, provisional term, in-world term, or naming suggestion.
- Prefer an ordinary existing word when it is equally good.
- Still propose a strong coinage when it materially improves the world or scene; simply mark its status clearly.

## Revision proposals

Use fixed IDs. Continue an existing revision-ID sequence if present; otherwise start at `R-001`.

Default diagnostic table:

| ID | Target | Current state | Problem | Proposal | Reason | Affected areas | Priority |
|---|---|---|---|---|---|---|---|
| R-001 | E03-S04 | ... | ... | ... | ... | E03, F07 | High |

Priorities:
- **High**: causality, chronology, motivation, climax logic, missing setup, contradictions that can break reader trust.
- **Medium**: character emphasis, payoff strength, pacing, information staging, redundancy.
- **Low**: wording, naming, card organization, optional elegance.

For a large change, compare at least:
- conservative option;
- middle option;
- bold option.

Do not edit canon solely because one option is preferred. Mark all unapproved options as proposals.

## Preferred report structure

Adapt to the task, but default to:

1. **Overall assessment** — what works and what should be preserved.
2. **High-priority findings** — causal/time-order/motivation issues first.
3. **Episode and Scene findings** — show exact affected IDs.
4. **Character/POV/information-state findings.**
5. **Foreshadowing and payoff map.**
6. **Theme and climax test.**
7. **World-rule and file-structure findings.**
8. **Revision proposal table.**
9. **Suggested revised flow** when useful.
10. **Artifact links** when generated.

Use prose around the table to explain the few most important findings. Do not dump an undifferentiated issue list.

See `references/review-rubric.md` for the detailed review checklist and `references/output-contract.md` for artifact conventions.

## Comparison-artifact workflow

When the user asks for a revised `.pltr` or when a comparison copy would materially help:

1. Copy the source to a new proposal file; never modify the source in place.
2. Preserve existing IDs and references whenever possible.
3. Make only substantive proposed changes that are explicitly described in the review and fall within the minimal write scope.
4. Keep unapproved `R-###` proposals in the review report by default. Do not modify the in-project revision-history Note merely to record proposals unless the user explicitly wants that.
5. Inspect the changed-object list before delivery. Revert every change that is unrelated to the named target or a necessary dependency; also revert formatting-only and no-op edits.
6. Apply the writing pass above to the changed descriptions, especially PL-01. Remove review-only validation from those passages; retain it only in the external report when useful. Check every changed paragraph against the source for substantive drift.
7. Run `scripts/sanitize_plottr.py <proposal-working.pltr> <proposal.pltr>` after all rich-text edits. By default, clear transient `ui.timeline.focus` editor selections; stale Slate selection paths can crash Plottr after descriptions change. Never guess replacement cursor paths.
8. Re-run `scripts/inspect_plottr.py` on the sanitized proposal. Treat rich-text errors and stale editor-selection references as delivery blockers.
9. Generate a comparison HTML with `scripts/compare_plottr.py <original.pltr> <proposal.pltr> <comparison.html>` when useful. It should show changed objects only, not “No changes” placeholders.
10. Package review outputs with `scripts/build_review_bundle.py` if a ZIP is useful.
   - Include proposal `.pltr`, comparison HTML, review Markdown/HTML, and validation report as available.
   - **Exclude the original `.pltr` by default.**
11. State that the proposal file is not canon until the user approves it.

## File-editing safeguards

- Preserve UTF-8 text.
- Preserve unknown top-level Plottr keys.
- Prefer surgical JSON edits over rebuilding the entire file.
- Treat `ui.timeline.focus` as disposable transient editor state in revised files. After changing rich-text descriptions, clear it before delivery unless explicitly requested otherwise.
- Never leave primitive values such as `false`, `null`, strings, or numbers as rich-text child nodes. Element nodes must contain `children` lists and text leaves must contain string `text`.
- Keep card/beat/line/tag/character/place IDs stable unless a new object requires a new ID.
- If removing a card from active use, prefer preserving its content in an explicitly labeled unused/unplaced area when the project's conventions support that, rather than silently deleting potentially valuable writing.
- Validate after edits.
- If Plottr application-level round-trip testing is unavailable, say so explicitly; JSON validation is not the same as opening and resaving in Plottr.

## Bundled references

- `references/canonical-template.md`: the user's Plottr long-form project standard that motivated this workflow. Use when compatible with the current project; do not force its story method onto unrelated projects unless the user wants it.
- `references/review-rubric.md`: detailed cross-project review checklist.
- `references/output-contract.md`: comparison and review artifact requirements.
- `references/prose-style.md`: compact scene prose, emotional register, and required use of the installed prose guard when accessible.
- `references/plottr-format-notes.md`: practical notes about observed `.pltr` JSON structure.

## Bundled scripts

- `scripts/inspect_plottr.py`: structural `.pltr` audit and Markdown/JSON report.
- `scripts/lint_plottr_prose.py`: read-only, changed-description prose review hints; inspect flags manually.
- `scripts/sanitize_plottr.py`: rich-text validation and stale-focus cleanup; preserve file metadata by default.
- `scripts/compare_plottr.py`: readable HTML comparison by beats/cards/notes/characters plus structural summary.
- `scripts/build_review_bundle.py`: ZIP selected review outputs while excluding the original source by default.
