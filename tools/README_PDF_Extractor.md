# Advanced PDF Content Extractor

A sophisticated Python tool for extracting tables and figures from complex, multi-layered PDF documents using state-of-the-art extraction libraries.

## Features

🔍 **Layer-Aware Extraction**: Handles complex PDFs with multiple layers  
📋 **Multi-Method Table Extraction**: Uses Tabula, Camelot, and pdfplumber  
🖼️ **Advanced Figure Extraction**: Vector graphics (SVG) + high-res rendering  
📊 **Rich Reporting**: Markdown report with image previews and table samples  
🤖 **Smart Detection**: Heuristic analysis to identify tables vs figures  
⚡ **CLI Interface**: Easy-to-use command line interface  

## Installation

### Requirements
- Python 3.12+
- Java Runtime Environment (for Tabula)

### Setup
```bash
# 1. Create virtual environment
python3.12 -m venv pdf_extraction_env

# 2. Activate environment
source pdf_extraction_env/bin/activate  # Linux/Mac
# or
pdf_extraction_env\Scripts\activate     # Windows

# 3. Install dependencies from requirements file
pip install -r requirements-pdfextractor.txt

# Alternative: Manual installation
pip install tabula-py camelot-py[cv] PyMuPDF pdfplumber pandas numpy Pillow opencv-python
```

## Usage

### Basic Usage
```bash
# Extract from PDF to default directory (extracted_content_FILENAME)
python advanced_pdf_extractor.py document.pdf

# Extract with verbose output
python advanced_pdf_extractor.py PDF_Proof.PDF --verbose

# Extract to custom directory
python advanced_pdf_extractor.py report.pdf --output my_extraction
```

### Command Line Options
```
usage: advanced_pdf_extractor.py [-h] [-o OUTPUT_DIR] [-v] [--version] pdf_file

positional arguments:
  pdf_file              Path to the PDF file to extract content from

options:
  -h, --help            Show help message
  -o OUTPUT_DIR         Output directory (default: extracted_content_FILENAME)
  -v, --verbose         Enable verbose output
  --version             Show version number
```

## Output Structure

The tool creates a comprehensive directory structure:

```
extracted_content_FILENAME/
├── tables/                 # CSV files with extracted table data
│   ├── tabula_lattice_table_1.csv
│   ├── camelot_stream_table_2.csv
│   └── pdfplumber_page_5_table_1.csv
├── figures/                # PNG and SVG files with extracted figures
│   ├── figure_page_1_highres.png    # High-resolution renders
│   ├── figure_page_2_vector.svg     # Vector graphics
│   └── embedded_page_3_img_1.png    # Embedded images
├── raw_data/               # Intermediate processing files
├── EXTRACTION_REPORT.md    # Comprehensive report with previews
└── extraction_report.json  # Machine-readable results
```

## Extraction Methods

### Table Extraction
- **Tabula**: Best for form-based tables and structured data
- **Camelot**: Excellent for complex layouts and scientific papers
- **pdfplumber**: Precise text extraction and simple tables

### Figure Extraction
- **SVG Vector**: Extracts vector graphics from all PDF layers
- **High-Resolution Render**: 3x scaling for figure-rich pages
- **Embedded Images**: Extracts actual embedded image files

## Report Features

The generated `EXTRACTION_REPORT.md` includes:
- 📊 **Summary statistics** and method performance
- 🖼️ **Image gallery** with PNG previews  
- 📋 **Table previews** showing first 10 rows as Markdown tables
- 📁 **Complete file listing** with paths and metadata

## Examples

### Example 1: Academic Paper
```bash
python advanced_pdf_extractor.py research_paper.pdf --verbose
```
**Output**: `extracted_content_research_paper/` with tables and figures

### Example 2: Custom Directory
```bash
python advanced_pdf_extractor.py complex_report.pdf -o report_extraction
```
**Output**: `report_extraction/` with extracted content

### Example 3: Processing PDF_Proof.PDF
```bash
python advanced_pdf_extractor.py PDF_Proof.PDF
```
**Result**:
- 📋 **126 tables** extracted (65 Tabula + 55 Camelot + 6 pdfplumber)
- 🖼️ **67 figures** extracted (46 vector + 19 high-res + 2 embedded)
- 📁 Output in `extracted_content_PDF_Proof/`

## Troubleshooting

### Common Issues
1. **Missing Dependencies**: The tool gracefully handles missing packages
2. **Java not found**: Install OpenJDK 11+ for Tabula support
3. **Font warnings**: Normal for complex PDFs, extraction continues
4. **Memory usage**: Large PDFs may require more RAM

### Dependency Management
The tool is designed to show help and version information even without dependencies:

```bash
# These work without any packages installed:
python advanced_pdf_extractor.py --help     # ✅ Always works
python advanced_pdf_extractor.py --version  # ✅ Always works

# This shows helpful error if dependencies missing:
python advanced_pdf_extractor.py document.pdf
# ❌ Error: Required dependency not found: No module named 'pandas'
# 📦 To install all required dependencies, run:
# pip install -r requirements-pdfextractor.txt
```

### Font Warnings
Font warnings like "Start marker missing" are common with academic PDFs and don't affect extraction quality.

## Performance

**PDF_Proof.PDF Results** (46 pages):
- ⏱️ **Processing time**: ~2 minutes
- 📊 **Success rate**: 126 tables + 67 figures extracted
- 🎯 **Methods used**: All extraction methods successfully applied
- 💾 **Output size**: ~15MB (high-resolution images included)

## Technical Details

### Dependencies
- `tabula-py`: Java-based table extraction
- `camelot-py[cv]`: Computer vision table detection
- `PyMuPDF`: PDF manipulation and rendering
- `pdfplumber`: Text-based PDF analysis
- `pandas`: Data manipulation
- `numpy`: Numerical operations
- `Pillow`: Image processing
- `opencv-python`: Computer vision

### File Naming Convention
- **Tables**: `{method}_{type}_table_{id}.csv`
- **Figures**: `figure_page_{page}_{type}.{ext}`
- **Output**: `extracted_content_{clean_filename}/`

## License

This tool is designed for academic and research use with complex PDF documents.

---

**Version**: 2.0  
**Python**: 3.12+  
**Last Updated**: August 2025