# script to replace placeholders in REPLICATION.md with generated content
import os
import shutil
import argparse

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
            with open(os.path.join(args.indir, filename), encoding="utf-8", mode='r') as f:
                replacement = f.read()
                template = replace_content(template,replacement,filename)
    # when we are done, we write it out
    with open(args.outfile, 'w') as f:
        f.write(template)

    
    
