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

def replace_content(template,replacement,tag):
    begin = BEGIN_MARKER.format(tag=tag)
    end = END_MARKER.format(tag=tag)
    wrapped = f"{begin}\n{DO_NOT_EDIT_NOTICE}\n{replacement.strip()}\n{end}"

    # If a previously-inserted fragment for this tag already exists, replace
    # just the content between its markers with the (possibly updated) content.
    marker_pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    if marker_pattern.search(template):
        return marker_pattern.sub(lambda m: wrapped, template)

    # Otherwise, this is the first insertion: replace the raw "{{ tag }}"
    # placeholder with the marker-wrapped content.
    placeholder = "{{ "+tag+" }}"
    if placeholder in template:
        return template.replace(placeholder, wrapped)

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

    
    
