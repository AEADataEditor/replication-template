# script to replace placeholders in REPLICATION.md with generated content
import os
import re
import shutil
import argparse

try:
    import chardet
except ImportError:
    chardet = None

TEMPLATE='REPLICATION.md'

# Fragments inserted by this script are wrapped in HTML comment markers so that
# later runs can find and replace them again, even after the original
# "{{ tag }}" placeholder has already been consumed. This keeps repeated runs
# idempotent: re-running with unchanged generated content leaves the file
# byte-for-byte identical (git neutral), while changed content updates only
# the fragment between the markers, leaving surrounding human edits alone.
BEGIN_MARKER = "<!-- BEGIN GENERATED: {tag} -->"
DO_NOT_EDIT_NOTICE = "<!-- Auto-generated content; do not edit by hand, changes will be overwritten -->"
END_MARKER = "<!-- END GENERATED: {tag} -->"

# A Markdown code-fence line: three or more backticks or tildes, optionally
# indented, optionally followed by an info string.
FENCE_RE = re.compile(r"[ \t]*(?:`{3,}|~{3,})[^\n]*")


def _line_bounds(text, start, end):
    """Widen [start:end] to whole-line boundaries."""
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    return line_start, line_end


def _enclosing_fences(text, line_start, line_end):
    """If the line(s) [line_start:line_end] are immediately wrapped by a pair of
    code-fence lines, return (open_start, open_fence, close_end, close_fence);
    otherwise None. The fences are pulled *inside* the generated markers so the
    HTML comment markers always render (they are invisible inside a code fence)."""
    if line_start == 0:
        return None
    prev_start = text.rfind("\n", 0, line_start - 1) + 1
    prev_line = text[prev_start:line_start - 1]
    if line_end >= len(text):
        return None
    next_end = text.find("\n", line_end + 1)
    if next_end == -1:
        next_end = len(text)
    next_line = text[line_end + 1:next_end]
    if FENCE_RE.fullmatch(prev_line) and FENCE_RE.fullmatch(next_line):
        return prev_start, prev_line, next_end, next_line
    return None


def _inner_fences(block):
    """Given the full text of an existing BEGIN..END marker block, return the
    (open_fence, close_fence) lines if its generated content is itself fenced,
    so a re-run can preserve the fence instead of dropping it. Otherwise
    ("", "")."""
    lines = block.split("\n")
    # lines[0] is the BEGIN marker; lines[-1] is the END marker.
    inner = lines[1:-1]
    if inner and inner[0] == DO_NOT_EDIT_NOTICE:
        inner = inner[1:]
    if len(inner) >= 2 and FENCE_RE.fullmatch(inner[0]) and FENCE_RE.fullmatch(inner[-1]):
        return inner[0], inner[-1]
    return "", ""


def _wrap(begin, end, replacement, open_fence="", close_fence=""):
    parts = [begin, DO_NOT_EDIT_NOTICE]
    if open_fence:
        parts.append(open_fence)
    parts.append(replacement.strip())
    if close_fence:
        parts.append(close_fence)
    parts.append(end)
    return "\n".join(parts)


def replace_content(template,replacement,tag):
    begin = BEGIN_MARKER.format(tag=tag)
    end = END_MARKER.format(tag=tag)

    # If a previously-inserted fragment for this tag already exists, replace
    # just the content between its markers with the (possibly updated) content.
    # An older version of this script could leave the markers *inside* a code
    # fence; detect that case and hoist the fences inside the markers instead.
    marker_pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    m = marker_pattern.search(template)
    if m:
        line_start, line_end = _line_bounds(template, m.start(), m.end())
        fences = _enclosing_fences(template, line_start, line_end)
        if fences:
            open_start, open_fence, close_end, close_fence = fences
            return (template[:open_start]
                    + _wrap(begin, end, replacement, open_fence, close_fence)
                    + template[close_end:])
        open_fence, close_fence = _inner_fences(m.group(0))
        return (template[:m.start()]
                + _wrap(begin, end, replacement, open_fence, close_fence)
                + template[m.end():])

    # Otherwise, this is the first insertion: replace the raw "{{ tag }}"
    # placeholder with the marker-wrapped content. If the placeholder sits on
    # its own line inside a code fence, place the markers outside the fence.
    placeholder = "{{ "+tag+" }}"
    idx = template.find(placeholder)
    if idx != -1:
        line_start, line_end = _line_bounds(template, idx, idx + len(placeholder))
        before = template[line_start:idx].strip()
        after = template[idx + len(placeholder):line_end].strip()
        on_own_line = not before and not after

        # A template may hide an optional placeholder inside an HTML comment
        # (`<!-- {{ tag }} -->`) so that an unfilled placeholder renders as
        # nothing. On fill, drop the comment delimiters and emit the markers on
        # their own lines.
        if before == "<!--" and after == "-->":
            return (template[:line_start]
                    + _wrap(begin, end, replacement)
                    + template[line_end:])

        fences = _enclosing_fences(template, line_start, line_end) if on_own_line else None
        if fences:
            open_start, open_fence, close_end, close_fence = fences
            return (template[:open_start]
                    + _wrap(begin, end, replacement, open_fence, close_fence)
                    + template[close_end:])
        return template.replace(placeholder, _wrap(begin, end, replacement))

    # Neither a placeholder nor previously-inserted markers were found: leave
    # the template untouched (the fragment isn't referenced anywhere).
    return template


            
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Replace tags with replacement text')
    parser.add_argument('--outfile', type=str, default=TEMPLATE,    help='File to write output to')
    parser.add_argument('--infile',  type=str, default=TEMPLATE,    help='File to use as template input')
    parser.add_argument('--indir',   type=str, default='generated', help='Directory containing replacement files. All files will be read.')
    
    args = parser.parse_args()
    print("Input:        ",args.infile)
    print("Output:       ",args.outfile)
    print("Reading from: ",args.indir)

    # read template
    with open(args.infile, encoding="utf-8", mode='r') as f:
        template = f.read()
    
    # Iterate over all files in a directory, read, then replace tag
    for filename in os.listdir(args.indir):
        if ( filename.endswith(".txt") or filename.endswith(".md") ):
            filepath = os.path.join(args.indir, filename)
            # Detect encoding automatically
            with open(filepath, 'rb') as f:
                rawdata = f.read()
                if chardet:
                    detected = chardet.detect(rawdata)
                    encoding = detected['encoding'] or 'utf-8'  # Default to utf-8 if detection fails
                    confidence = detected['confidence']
                else:
                    encoding = 'utf-8'
                    confidence = 1.0
            
            # Warn if encoding is not UTF-8 or confidence is low
            if encoding.lower() not in ['utf-8', 'utf-8-sig', 'ascii']:
                print(f"Warning: {filename} detected as {encoding} (confidence: {confidence:.2f})")
            
            # Read file with detected encoding, fall back to latin-1 if it fails
            try:
                with open(filepath, encoding=encoding, mode='r') as f:
                    replacement = f.read()
            except (UnicodeDecodeError, LookupError):
                print(f"Warning: {filename} failed with {encoding}, using latin-1 fallback")
                with open(filepath, encoding="latin-1", mode='r') as f:
                    replacement = f.read()
            
            template = replace_content(template,replacement,filename)
    # when we are done, we write it out
    with open(args.outfile, 'w', encoding='utf-8') as f:
        f.write(template)

    
    
