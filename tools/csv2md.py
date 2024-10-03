#!/usr/bin/python3
# Tool to convert arbitrary CSV to Markdown

import csv
from argparse import ArgumentParser



def try_utf8(filehdl):
    "Returns a Unicode object on success, or None on failure"
    try:
       data = filehdl.read()
    except UnicodeDecodeError:
       return None
    
    if not data:
        return None
    
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return None

def blank_md(md_file,message):
    # CSV is empty, write message to Markdown file
    with open(md_file, 'w') as f:
        f.write(message)
        exit()

def csv_to_markdown(csv_file, md_file):
    with open(csv_file, 'rb') as f:
        utfdata = try_utf8(f)
        if utfdata is None:
            print("Error: CSV file is not UTF-8 encoded")
            blank_md(md_file,"Output of parser is not UTF-8 encoded")
            
    # the file should be fine, let's read it again
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            print("NOTE: CSV file is empty")
            blank_md(md_file,"No data.")

    # All exceptions should be handled, lets continue

    headers = [key for key in rows[0].keys()]

    md_table = f'| {" | ".join(headers)} |\n' 
    md_table += f'| {" | ".join(["---"]*len(headers))} |\n'
  
    for row in rows:
        md_table += f'| {" | ".join(str(x) for x in row.values())} |\n'

    with open(md_file, 'w') as f:
        f.write(md_table)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('csv_file')
    args = parser.parse_args()

    md_file = args.csv_file.replace('.csv', '.md')
    csv_to_markdown(args.csv_file, md_file)