# Optional appendix: figures with cosmetic differences

Read when the RA's `### Tables and Figures` marks figures as reproduced with
differences (axis ranges, tick intervals, misplaced labels or arrows). Whoever
reads the report decides whether the figures should be adjusted, not the
replicator; this appendix gives them what they need to decide.

**Optional, needs approval.** Offer it with `AskUserQuestion`; never add it by
default. Batch mode: list it as a numbered decision.

## Which figures

Include a figure only when the replicator noted a difference beyond tick
intervals: a different axis range, misplaced labels or arrows, and the like. If
the only finding is "same range, different intervals", leave it out entirely.
Also leave out figures that were not reproduced and figures with no program.

## Layout (plain Markdown: no tables, no HTML, no commentary)

One `### Figure N` heading per figure, a terse label on each side, manuscript
image on one line, produced panels on the next:

```
## Appendix: Figures with cosmetic differences

### Figure 5

Manuscript:
![](manuscript_parsed/PDF_Proof/_page_26_Figure_4.jpeg)

Produced:
![](<deposit>/project/Mechanism/Graphs/Figure5a.png) ![](<deposit>/project/Mechanism/Graphs/Figure5b.png)
```

Manuscript images are `manuscript_parsed/<doc>/_page_N_Figure_M.jpeg`; map them
to figure numbers through the captions in `manuscript_parsed/<doc>/<doc>.md`.
Produced panels come from the deposit. Add a one-line pointer to the appendix
from `### Tables and Figures`.

## Placement and checks

- Put it at the end of the narrative report, **before** `# Automatically
  Generated Appendices`: `24_amend_report.sh` truncates from that line onward.
- Before finishing, check that every referenced image exists and is tracked by
  git. Produced PNGs may be gitignored; see
  [gitignored-files.md](gitignored-files.md) (ask first).
