#!/bin/bash

# mk_tex_table.sh - Convert standalone LaTeX table files to PDF documents
#
# DESCRIPTION:
#   This script processes standalone LaTeX table files (.tex) and converts them
#   to complete PDF documents. It wraps each table with a full LaTeX document
#   structure including necessary packages for table formatting and compiles
#   them to PDF using pdflatex.
#
# USAGE:
#   ./mk_tex_table.sh
#
# INPUT:
#   - All .tex files in the current directory (excluding those prefixed with "pdf_")
#   - Files should contain LaTeX table code (tabular, table, etc.)
#
# OUTPUT:
#   - pdf_{original_filename}.tex - Complete LaTeX documents with headers
#   - pdf_{original_filename}.pdf - Compiled PDF files
#   - Additional LaTeX compilation files (.aux, .log, etc.)
#
# BEHAVIOR:
#   - Scans current directory for .tex files
#   - Excludes files already prefixed with "pdf_" to avoid reprocessing
#   - Creates complete LaTeX documents with comprehensive package imports
#   - Compiles each document to PDF using pdflatex
#
# PACKAGES INCLUDED:
#   - inputenc: UTF-8 encoding support
#   - eurosym: Euro symbol support
#   - graphicx: Graphics inclusion
#   - geometry: Page layout (landscape, 0.5in margins)
#   - hyperref: Hyperlink support
#   - xcolor: Color support
#   - subfig: Subfigure support
#   - caption: Enhanced captions
#   - booktabs: Professional table formatting
#   - threeparttable: Three-part table support
#   - float: Float positioning
#   - adjustbox: Box adjustments
#   - supertabular: Multi-page tables
#
# DEPENDENCIES:
#   - pdflatex (TeX Live or similar LaTeX distribution)
#   - Standard Unix utilities (ls, grep, cat, echo)
#
# EXAMPLE:
#   If directory contains "results.tex" and "summary.tex":
#   - Creates "pdf_results.tex" and "pdf_summary.tex" with full document structure
#   - Compiles to "pdf_results.pdf" and "pdf_summary.pdf"

# Process all .tex files in current directory, excluding those already prefixed with "pdf_"
for arg in $(ls *tex | grep -v pdf_)
do
    # Create complete LaTeX document with comprehensive package imports
    echo "\documentclass{article}
	\usepackage[utf8]{inputenc}
	\usepackage{eurosym}
	\usepackage{graphicx}
	\usepackage[landscape,margin=0.5in]{geometry}
        \usepackage{hyperref}
	\usepackage{xcolor}
	\usepackage{subfig}
	\usepackage{caption}
	\usepackage{booktabs}
	\usepackage{threeparttable}
	\usepackage{caption}
	\usepackage{float}
	\usepackage{adjustbox}
	\usepackage{supertabular}
	\begin{document}
	" > pdf_$arg
    
    # Append the original table content
    cat $arg >> pdf_$arg
    
    # Close the LaTeX document
    echo "\end{document}" >> pdf_$arg
    
    # Compile the complete document to PDF
    pdflatex pdf_$arg
done
