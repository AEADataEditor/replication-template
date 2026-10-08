---
name: aea-replication-run
description: Use when actually RUNNING an author's replication package during an AEA Data Editor review — running the deposit's own master file or building one where none exists, locating and wiring up restricted-access data, executing the code under containerized Stata, iterating on failures, verifying the reported numbers against the manuscript, and writing the results into REPLICATION.md's Findings/Replication steps/Classification sections. Triggers on "run the replication package", "run the author's code", "does this deposit run", "the code failed at X", "verify the numbers", "check the tables against the paper", "build a master.do", "where is the restricted data", "resume the replication", or being handed an aearep-NNNN repo whose REPLICATION.md is not yet filled in. This is the stage BEFORE the report is finalized — hand off to aea-report-finalize once Findings and Classification reflect what actually happened.
---

# Running an AEA Replication Package

You are the replicator. Your job is to find out whether the deposited code
actually runs, whether it actually produces the numbers in the paper, and to
write down what you found — precisely enough that the editor can act on it.

Where this sits: the pipeline has already downloaded the deposit and filled the
report's scan appendices. You run the code and fill in the narrative sections.
Then `aea-report-finalize` consolidates tags and drafts the SUMMARY. Don't do
its job — no SUMMARY, no `aeaready`, no approval commit.

## Orient before touching anything

Derive everything from the repo rather than assuming. The deposit is the
bare-numeric directory at the repo root; `config.yml` carries `openicpsr:` and
`jiraticket:`. Read `REPLICATION.md` first — a prior round may have already
recorded findings, and on a revision round the ticket in `config.yml` may be
newer than the one in the directory name.

Then read the deposit's README and inventory the code. Two questions shape
everything that follows: **is there a master file**, and **is any of the data
restricted**. Answer both before writing anything.

## Is there already a master file?

Look before you build. Many deposits do ship a driver, and running the authors'
own entry point is always preferable to substituting your own — it's what a real
replicator would do, and a driver you invent can mask ordering assumptions the
authors relied on.

```bash
ls <deposit>/{main,master,run,runall,_master}*.* 2>/dev/null
grep -rlEi '^\s*(do|include)\s' <deposit> --include='*.do' | head
```

The README usually says. A file that `do`s many others is the master even if it
isn't named like one.

**If one exists**, use it. Fix what breaks; don't replace it. If it only covers
part of the package, say so as a finding rather than quietly widening it.

**If none exists**, that absence is itself a finding — record it, and check
whether a `[SUGGESTED]`/`[REQUIRED]` main-control-file tag already exists from a
prior round. Then build one so the package can be run end to end, keeping your
scaffolding separate from the authors' code so the diff stays honest about what
you changed.

**`config.do`** — copy the repo's `template-config.do` and set the scenario to
match where your master file sits relative to the code directories. Its
`ssc_packages` local is where every third-party dependency gets declared; you
will be adding to it as failures surface.

**`master.do`** — call every program in the authors' numbered order:

```stata
include "config.do"
global data "${rootdir}/data"
global outp "${rootdir}/output"     // define globals the authors reference but never set
cap mkdir "${outp}"
cd "${outp}"                         // so relative-path output doesn't litter code dirs

do "${rootdir}/Main-tables/1. Table 1.do"
do "${rootdir}/Main-tables/2. Table 2.do"
...
di as result "===== END MASTER ====="
```

Two deliberate choices. **Don't wrap calls in `cap`** — you want the run to stop
at the first failure so the log shows exactly where it died. And **echo a sentinel
at the end**, because that is how you will tell a completed run from a killed one.

Include files that ship misfiled (e.g. an appendix program sitting at the deposit
root) — running them is the point — but record the misfiling as a finding.

## Is there restricted data? (only then, wire it up)

Many packages have none — everything needed is in the deposit, and there is
nothing to do here. Skip this whole section in that case.

But the absence of a `restricted/` directory does **not** mean there's no
restricted data. It may simply not have been fetched yet. Jira is the authority
on whether restricted data is expected, so check it rather than inferring from
the filesystem:

```bash
python3 tools/jira_get_info.py <TICKET> dcaf_private   # "yes" if privately available
```

For the Box location, query the fields directly (`jira_get_info.py` doesn't
expose them):

| Field | Meaning |
|---|---|
| `customfield_10518` | Restricted data Box **Folder ID** — the one you pass to the download tools |
| `customfield_10352` | Restricted data Box location (human-readable URL) |
| `customfield_10115` | `DCAF_Access_Restrictions_V2` — how obtainable, and whether it can be shared privately |
| `customfield_10093` | Working location of restricted data |

```bash
curl -s -u "$JIRA_USERNAME:$JIRA_API_KEY" -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/issue/<TICKET>?fields=customfield_10518,customfield_10352,customfield_10115"
```

**A populated Box Folder ID with no local `restricted/` means the data exists and
you haven't got it yet** — fetch it rather than concluding the package can't be
run:

```bash
python3 tools/list_box_files.py <NNNN>        # inspect before downloading
python3 tools/download_box_private.py <NNNN>  # lands in ./restricted by default
```

If Jira says restricted data should exist but no Box folder is recorded and none
arrived, that's a finding and a question for the editor — not something to work
around silently.

### Getting it where Stata can see it

The container mounts only the deposit directory, so data outside it is invisible.
Keep restricted files out of the deposit proper (they must never reach git) and
link them in:

```bash
mkdir -p <deposit>/data
ln <restricted-dir>/<file>.dta <deposit>/data/<file>.dta
```

A hard link rather than a symlink, because a symlink pointing outside the mount
dangles inside the container; and rather than a copy, which wastes space and is
easier to commit by accident.

This is the easy case, and it often isn't the case you get. Expect to adapt:

- **Hard links need one filesystem.** If `restricted/` is on a different mount,
  `ln` fails outright — copy into the gitignored `data/` directory instead, or
  mount differently.
- **The code's expected location may not be `data/`.** Read what the programs
  actually `use` and place files to match, rather than reshaping the deposit.
  Where the authors hard-code an absolute path, note it as a finding.
- **What arrives may not be analysis-ready** — archives to expand, several files
  where the code expects one, or a name that differs from what the code opens.
  Renaming to satisfy the code is a change worth recording.
- **Some data can't leave its secure environment at all.** Then the run happens
  there, or not at all; say so plainly in the report instead of improvising.

Whatever the shape, confirm `.gitignore` covers `**/data/*` and `*.dta`, and
verify with `git check-ignore -v <path>` before the first run. This check is
cheap and the failure mode — restricted data committed to a shared repo — is not
recoverable by deleting the file.

## Running containerized Stata

The `stata*` wrappers in `~/bin/aea-scripts/` are `docker run -it --rm -v
"$(pwd)":/project -w /project`. Four things will bite you, and three of them cost
real time to diagnose because the symptom points somewhere else.

**Permissions — the expensive one.** The container runs as `uid=2000(statauser)
gid=100(users)`. Much guidance says `chmod -R o+w`, which yields `drwxr-xrwx`.
That is not enough when the host user's group is *also* gid 100: POSIX matches the
**group** class first and never falls through to the `other` bits. Stata then
can't create its log and dies before executing a line, while the wrapper still
exits 0. Use:

```bash
chmod -R go+w <deposit>
```

Check with `id`. This mimics an SELinux bind-mount denial closely enough to send
you chasing `:z`/`:Z` for an hour. To tell them apart, test with the *actual*
Stata image — a generic `--user 2000 alpine` container gets `gid=0`, falls through
to the `other` bits, and misleadingly succeeds:

```bash
docker run --rm -v "$(pwd)":/project -w /project --entrypoint /bin/bash \
  <stata-image> -c 'id; touch /project/_t && echo OK'
```

**TTY.** `-it` fails under a non-interactive shell. Wrap the call:

```bash
script -qec "stata19 -b do master.do" /dev/null </dev/null
```

**Stdin.** That `</dev/null` is not decoration. `script` reads stdin, so inside a
`while read` loop it will swallow the rest of your file list and you'll silently
process only the first item.

**Exit codes lie.** The wrapper ends with `system-info.sh`/`docker-info.sh`, which
return 0 no matter what happened inside. Always judge from the log:

```bash
grep -c "END MASTER" master.log          # sentinel present?
grep -nE "^r\([0-9]+\);" master.log      # Stata errors
grep -c '^\. do "' master.log            # programs actually executed
```

A log that stops mid-command with no `r(nnn);` and no `end of do-file` is a killed
container, not a Stata error — check `dmesg` for `oom-kill` naming `stata-mp`.
Memory failures are a property of the machine, not the code: confirm on a larger
host before recording anything about the code.

## Iterate on failures

The default loop is: run, fix or exclude the failure, commit the run output, run
again. What matters is the judgment about which failures you may fix yourself.

**Fix directly** when the correction is small and obviously right — a variable
name that doesn't match the data, a missing package declaration. Note it as a fix.

**Ask first** for anything larger — rewriting a specification, working around a
resource limit, restructuring the authors' logic. Recording a program as excluded
is also a decision worth surfacing rather than making unilaterally.

**Commit each iteration** as one bundle: the code fix, the REPLICATION.md note,
and the run output (`logs/`, `ado/`, `master.log`, `output/`). Stage explicit
paths — never `git add -A`, which will sweep in data. Don't stage a log while a
run is still writing it.

**Re-read `REPLICATION.md` immediately before editing it.** The editor may be
editing it concurrently in an IDE; blind overwrites lose their work.

### When a full run is expensive

A package with bootstrap-heavy programs can take 15 hours per pass, which makes
"re-run everything after each fix" untenable when a dozen failures remain. A
faster shape, worth proposing rather than assuming:

1. **Sweep every program in isolation** — each in its own container, its own log,
   not stopping at the first failure. One pass yields the complete failure
   inventory instead of one bug at a time. `scripts/sweep-programs.sh` does this.
2. **Fix everything the sweep found**, then run the section sequentially to catch
   any cross-file ordering dependency isolation can't see.
3. **One full end-to-end run** for the single clean log the review needs.

Isolation is safe when each program starts with `clear all` and its own `use` —
check that assumption before relying on it.

Classify sweep results by grepping each log for a sentinel you echo yourself. The
wrapper's exit code is no more trustworthy here than anywhere else.

## Verify the numbers, not just that it ran

**Code that runs is not code that reproduces.** Until output is compared to the
manuscript, you know only that nothing errored. Don't let a clean run drift into a
claim of reproduction.

Extract the manuscript text and work table by table:

```bash
pdftotext -layout <proof>.pdf proof.txt
grep -nE "TABLE [0-9]+" proof.txt
```

Then pull each table's output from the log and compare cell by cell. Some traps:

- **Stata wraps long lines** with a `>` continuation, so an exact `grep` for a
  long `do "..."` line or command silently misses. Flatten before matching.
- **Long variable names are abbreviated** in output (`hasba~brank5`), so grepping
  the full name finds nothing. Search on the visible stem.
- **Descriptive tables often aren't printed as such** — recompute the reported
  proportions from the cross-tabs the code does print.
- **Bootstrap p-values reproduce only if a seed is set.** Check for `set seed`;
  its absence is itself a finding.

Record what you verified *and what you couldn't*. Two patterns make numbers
unverifiable even when the code runs perfectly, and both are reportable findings:

- **`quiet`-suppressed estimation.** Coefficients and standard errors never reach
  the log; only post-estimation `test`/`lincom` output does.
- **No table export.** Grep the whole package for `esttab|estout|outreg2?|putexcel|
  export excel|mat2txt|asdoc`. If a package of 80 programs contains two such
  commands, essentially every number is meant to be read off a console that no
  longer exists.

Also watch for numbers computed into variables and never displayed — verifiable
only by re-deriving them, which a replicator shouldn't have to do.

## Write it into REPLICATION.md

Fill the narrative sections; leave the auto-generated appendix alone (everything
from `# Automatically Generated Appendices` down is regenerated at sign-off, so
edits there are discarded).

**`## Replication steps`** — what you actually did, in the past tense. If you
built a driver, say so. Include runtime and peak memory when notable, and state
plainly whether numerical agreement was assessed.

**`## Findings` → program-specific issues** — one line per issue:

```
- `path/to/file.do`: <what was wrong>. <what you did about it>.
```

**`### Missing Requirements`** — for undeclared dependencies, use the verbatim
setup-program tag from `sample-language-report.md` and put the specifics in an
untagged line beneath it. Don't paraphrase the tag into a custom one-liner; the
finalize skill lifts the tagged line verbatim into the action-item checklist.

Watch for **dependencies of dependencies**: `ssc install` does not resolve them,
so a package that itself requires another needs both declared, or the next
replicator fails at the same point.

**`## Classification`** — check exactly one box, and make sure it reflects the
current state rather than what was true before data arrived. Stale classifications
are common on revision rounds. Calibrate honestly:

- Everything ran *and* the numbers were checked and match → full reproduction.
- Ran clean, but a substantial share of numbers can't be checked, or some data is
  confidential and unavailable → partial reproduction.
- Reserve "not able to reproduce" for genuinely not getting the code to run.

Update `### Reason for incomplete reproducibility` to match — if you fixed
author-code bugs to get through, `Bugs in code` belongs checked.

## Hand off

When Findings, Replication steps, and Classification reflect reality, stop and
hand to `aea-report-finalize`. Leave the SUMMARY alone — that's the editor's
voice, and the finalize skill drafts it from the tags you left.

## Bundled

- `scripts/sweep-programs.sh` — run each program in its own container, one log
  apiece, continuing past failures, emitting a PASS/FAIL summary. Read its header
  for usage; it already handles the stdin and exit-code traps above.
