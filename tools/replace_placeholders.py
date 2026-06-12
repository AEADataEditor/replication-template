# script to replace placeholders in REPLICATION.md with generated content
import os
import shutil
import argparse
import chardet

TEMPLATE='REPLICATION.md'

def replace_content(template,replacement,tag):
    new_content = template.replace("{{ "+tag+" }}", replacement)
    return new_content
    

            
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
                detected = chardet.detect(rawdata)
                encoding = detected['encoding'] or 'utf-8'  # Default to utf-8 if detection fails
                confidence = detected['confidence']
            
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

    
    
