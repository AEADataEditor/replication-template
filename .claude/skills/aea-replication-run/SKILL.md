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

Derive everything from the repo rather than assuming. The **package folder** is
the directory the source repository's download landed in, and its name depends on
the source: an openICPSR deposit is its bare project number (`123456`), others are
prefixed (`wb-…`, `dv-…`, `zenodo-…`, `osf-…`). Resolve it the way the pipeline
does instead of guessing from the directory listing:

```bash
. ./tools/resolve_project_id.sh     # sets $projectID from config.yml
```

`config.yml` also carries `jiraticket:`. Read `REPLICATION.md` first — a prior
round may have already recorded findings, and on a revision round the ticket in
`config.yml` may be newer than the one in the directory name. If the report has
been split (`REPLICATION-PartA.md`/`REPLICATION-PartB.md` exist), the narrative
sections live in Part B: `automations/50_merge-parts.sh` regenerates
`REPLICATION.md` from the two parts, so edits to it would be lost.

Then read the package's README and inventory the code. Two questions shape
everything that follows: **is there a master file**, and **is any of the data
restricted**. Answer both before writing anything.

## Start in the package folder, then discover its conventions

Every run starts in the package folder: `cd "$projectID"` before launching
Stata, so the container mounts the whole package and every file the code might
open is visible. Never launch from a subdirectory (a `code/` or `programs/`
folder): the wrappers mount only the current directory, so data in a sibling
directory silently disappears.

From there, packages differ, and the layout must be discovered rather than
assumed. Read the code for:

- **Where the programs expect the working directory to be.** Relative `use`,
  `import`, `save`, and `include` paths only resolve from one place — sometimes
  the package root, sometimes a code subdirectory, sometimes a data folder.
- **How paths are built.** A root global the authors set at the top of a master
  (`global root "C:/Users/..."`), globals referenced but never defined, absolute
  paths hard-coded in individual programs, Windows backslashes.
- **Where output goes.** Some programs write next to themselves, some into
  `output/` or `results/` directories that may not exist yet.
- **Whether programs are independent.** Each one starting with `clear` and its
  own `use`, or relying on data left in memory or files written by an earlier
  program.

```bash
grep -rnEi '^\s*(cd|use|save|import|export|include|global)\b' "$projectID" --include='*.do' | head -50
```

Adapt the run to what you find — `cd` inside Stata to where the programs expect
to be, set the authors' root global to `${rootdir}`, create the output
directories they assume — rather than reshaping the package. Every hard-coded
path you replace is a finding.

## Is there already a master file?

Look before you build. Many deposits do ship a driver, and running the authors'
own entry point is always preferable to substituting your own — it's what a real
replicator would do, and a driver you invent can mask ordering assumptions the
authors relied on.

```bash
ls "$projectID"/{main,master,run,runall,_master}*.* 2>/dev/null
grep -rlEi '^\s*(do|include)\s' "$projectID" --include='*.do' | head
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

**`config.do`** — copy the repo's `template-config.do` into the package folder
and use scenario `B`, so `${rootdir}` is the package folder you launched from
(scenario `A` steps up one directory, which only works when Stata starts inside a
code subdirectory). Its `ssc_packages` local is where every third-party
dependency gets declared; you will be adding to it as failures surface.

**`master.do`** — in the package folder, call every program in the order the
README (or the file numbering) gives, adapted to the conventions you discovered.
The shape, not the specifics:

```stata
include "config.do"
* adapt to what the programs expect, for example:
*   global root "${rootdir}"          // a root global the authors set by hand
*   cap mkdir "${rootdir}/output"     // an output directory they assume exists
*   cd "${rootdir}/code"              // if relative paths assume the code folder

do "${rootdir}/<path>/<first program>.do"
do "${rootdir}/<path>/<second program>.do"
...
di as result "===== END MASTER ====="
```

When the authors ship a master in a subdirectory, launch from the package folder
anyway and call it by path (`stata19 -b do code/main.do`), with `include
"config.do"` added at its top; `include` resolves against the working directory,
which is still the package folder.

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

The container mounts only the package folder, so data outside it is invisible.
Keep restricted files out of the deposit proper (they must never reach git) and
link them in:

```bash
mkdir -p "$projectID"/data
ln <restricted-dir>/<file>.dta "$projectID"/data/<file>.dta
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
"$(pwd)":/project -w /project` — which is why every run is launched from the
package folder. Four things will bite you, and three of them cost real time to
diagnose because the symptom points somewhere else.

**Permissions — the expensive one.** The container runs as `uid=2000(statauser)
gid=100(users)`. Much guidance says `chmod -R o+w`, which yields `drwxr-xrwx`.
That is not enough when the host user's group is *also* gid 100: POSIX matches the
**group** class first and never falls through to the `other` bits. Stata then
can't create its log and dies before executing a line, while the wrapper still
exits 0. Use:

```bash
chmod -R go+w "$projectID"
```

Check with `id`. This mimics an SELinux bind-mount denial closely enough to send
you chasing `:z`/`:Z` for an hour. To tell them apart, test with the *actual*
Stata image — a generic `--user 2000 alpine` container gets `gid=0`, falls through
to the `other` bits, and misleadingly succeeds:

```bash
docker run --rm -v "$(pwd)":/project -w /project --entrypoint /bin/bash \
  <stata-image> -c 'id; touch /project/_t && echo OK'
```

**TTY.** `-it` fails under a non-interactive shell. Wrap the call, from the
package folder:

```bash
cd "$projectID"
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

**When a full pass is expensive** (hours per run, many failures left), propose a
plan to the editor before improvising a different way of running the package.

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
