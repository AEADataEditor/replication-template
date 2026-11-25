# TRO deposits — extra checks

Read when Step 2b found a TRO. TRO = JSON-LD in the deposit's `tro/` (SIVACOR
is one source) = a *trusted verification system*, a different box from
*trusted third party*.

```bash
ls generated/REPLICATION-PartB-SIVACOR.md
grep -n '{{ sivacor-partb-' REPLICATION.md
grep -n 'trusted verification system' REPLICATION.md
```

- **Part B generated** = file exists and no `{{ sivacor-partb-* }}` remain.
  Else flag in Step 6, naming `automations/28_sivacor_partb.sh`; don't
  generate or write it.
- **Box**: "trusted verification system" checked in `## Computing Environment
  of the Replicator` and `## Replication steps`; check it if content is
  present but box isn't. "Trusted third party" checked → ask.
- Never edit inside `BEGIN/END GENERATED` markers.
- **SUMMARY (Step 5.4)**: use the "trusted verification system" wording from
  `sample-language-report.md`, not the third-party wording.
- **Step 6**: report Part B generated?, and the box state.

## An unchanged hash is not evidence of regeneration

The TRO records content hashes per arrangement, not write events. An output
whose hash is identical before and after the workflow is consistent with the
code rewriting it byte-for-byte *or* never touching it. Before concluding
"regenerated and identical to the authors' shipped copy", cross-check at least
one of:

- the SIVACOR stdout/stderr capture (e.g. "… exported successfully");
- the code (`fopen(...,'w')`, `graph export … replace`, `esttab using … replace`);
- a companion file written later by the same program whose hash *did* change.

Only a hash that changes is direct TRO evidence that a file was written. With
none of the above, report the output as "unchanged, not shown to be
regenerated" and ask the editor; don't assert regeneration.
