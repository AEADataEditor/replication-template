# Manuscript action items: order check

Read after the last `aea-parse-tags` run (Step 4).

`### Action Items (manuscript)` must list the consolidated `- [ ]` items
**above** the fixed `[REQUIRED]` blockquotes ("If making changes to the
manuscript…", "When returning proofs, confirm…"), so the editor reads the
actionable items first. Upstream fix requested:
[editor-scripts#42](https://github.com/AEADataEditor/editor-scripts/issues/42).

**Check** (mechanical, don't ask): in that section, does the first `- [ ]` line
come before the first `>` line?

- **Yes** → nothing to do (a fixed `aea-parse-tags`, or no items).
- **No** → *workaround until #42 is released*: move the whole `- [ ]` block so
  it sits above those blockquotes, items and order unchanged, blockquotes left
  as they are (they stay `>`, never `- [ ]`). Say in Step 6 that you moved it,
  so we know the upstream fix hasn't landed.

Rerunning `aea-parse-tags` regenerates the lists, so redo the check after any
rerun.
