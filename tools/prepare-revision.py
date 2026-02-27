import re

def process_markdown_file(input_file, output_file):
    """
    Process a Markdown file by replacing only the code block content 
    in the specific Appendix section while maintaining the section header.

    Args:
        input_file (str): Path to the input Markdown file
        output_file (str): Path to the output Markdown file
    """
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Regex pattern to match the Appendix section
    # Captures the header and any text before the code block
    # Replaces only the content within the code block
    pattern = r'((\*\*## Appendix: Programs provided\*\*\n).*?\n)```[\s\S]*?```'
    replacement = r'\1```\n{{ programs-list.txt }}\n```'
    
    # Perform the replacement
    modified_content = re.sub(pattern, replacement, content, flags=re.MULTILINE|re.DOTALL)
    
    with open(output_file, 'w') as f:
        f.write(modified_content)
    
    print(f"Processed Markdown file saved to {output_file}")

# Example usage
process_markdown_file('REPLICATION.md', 'REPLICATION_modified.md')
