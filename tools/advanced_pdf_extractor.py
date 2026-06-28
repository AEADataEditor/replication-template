#!/usr/bin/env python3

"""
Advanced PDF Content Extractor
===============================

A sophisticated tool for extracting tables and figures from complex, multi-layered PDF documents.
Uses multiple extraction methods including Camelot, pdfplumber, tabula, and PyMuPDF for 
comprehensive content extraction.

Author: Advanced PDF Extractor
Version: 2.0
Dependencies: See requirements below

REQUIREMENTS:
- Python 3.12+
- Java Runtime (for tabula)
- Libraries: tabula-py, camelot-py[cv], PyMuPDF, pdfplumber, pandas, numpy, Pillow, opencv-python

INSTALLATION:
1. Create virtual environment: python3.12 -m venv pdf_extraction_env
2. Activate environment: source pdf_extraction_env/bin/activate  
3. Install dependencies: pip install tabula-py camelot-py[cv] PyMuPDF pdfplumber pandas numpy Pillow opencv-python

USAGE:
    python advanced_pdf_extractor.py input.pdf [--output OUTPUT_DIR] [--verbose] [--help]

EXAMPLES:
    # Extract from PDF_Proof.PDF to default directory
    python advanced_pdf_extractor.py PDF_Proof.PDF

    # Extract to custom directory
    python advanced_pdf_extractor.py document.pdf --output my_extraction

    # Verbose output
    python advanced_pdf_extractor.py document.pdf --verbose

OUTPUT:
Creates directory structure:
    extracted_content_FILENAME/
    ├── tables/          # CSV files with extracted table data
    ├── figures/         # PNG and SVG files with extracted figures
    ├── raw_data/        # Intermediate processing data
    ├── EXTRACTION_REPORT.md    # Comprehensive report with previews
    └── extraction_report.json  # Machine-readable results
"""

import argparse
import os
import sys
import json
import re
from pathlib import Path

# Defer heavy imports until after argument parsing
def _import_dependencies():
    """Import heavy dependencies only when needed"""
    global pd, np, fitz, tabula, camelot, pdfplumber, warnings
    
    try:
        import pandas as pd
        import numpy as np
        import fitz  # PyMuPDF
        import tabula
        import camelot
        import pdfplumber
        import warnings
        warnings.filterwarnings('ignore')
    except ImportError as e:
        print(f"❌ Error: Required dependency not found: {e}")
        print("\n📦 To install all required dependencies, run:")
        print("pip install -r requirements-pdfextractor.txt")
        print("\nAlternative (manual install):")
        print("pip install tabula-py camelot-py[cv] PyMuPDF pdfplumber pandas numpy Pillow opencv-python")
        print("\n💡 Or see installation instructions:")
        print("python advanced_pdf_extractor.py --help")
        sys.exit(1)

class AdvancedPDFExtractor:
    def __init__(self, pdf_path, output_dir=None, verbose=False):
        self.pdf_path = pdf_path
        self.verbose = verbose
        
        # Generate smart output directory name if not provided
        if output_dir is None:
            pdf_name = Path(pdf_path).stem
            # Clean the filename for directory name
            clean_name = re.sub(r'[^\w\-_]', '_', pdf_name)
            clean_name = re.sub(r'_+', '_', clean_name).strip('_')
            self.output_dir = f"extracted_content_{clean_name}"
        else:
            self.output_dir = output_dir
            
        self.results = {
            'tables': [],
            'figures': [],
            'metadata': {},
            'extraction_methods': []
        }
        
        # Create output directories
        Path(self.output_dir).mkdir(exist_ok=True)
        Path(f"{self.output_dir}/tables").mkdir(exist_ok=True)
        Path(f"{self.output_dir}/figures").mkdir(exist_ok=True)
        Path(f"{self.output_dir}/raw_data").mkdir(exist_ok=True)
        
    def _log(self, message, force=False):
        """Print message if verbose mode is enabled"""
        if self.verbose or force:
            print(message)
        
    def analyze_pdf_structure(self):
        """Analyze the PDF structure to understand complexity"""
        self._log("🔍 Analyzing PDF structure...")
        
        doc = fitz.open(self.pdf_path)
        self.results['metadata'] = {
            'total_pages': len(doc),
            'title': doc.metadata.get('title', ''),
            'subject': doc.metadata.get('subject', ''),
            'creator': doc.metadata.get('creator', ''),
            'producer': doc.metadata.get('producer', ''),
        }
        
        # Analyze each page
        page_analysis = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get all drawing objects (including layers)
            drawings = page.get_drawings()
            images = page.get_images()
            text_blocks = page.get_text_blocks()
            
            analysis = {
                'page': page_num + 1,
                'drawings_count': len(drawings),
                'images_count': len(images),
                'text_blocks': len(text_blocks),
                'has_complex_graphics': len(drawings) > 5,
                'likely_has_table': self._detect_table_heuristic(page),
                'likely_has_figure': self._detect_figure_heuristic(page, images, drawings)
            }
            page_analysis.append(analysis)
            
        self.results['page_analysis'] = page_analysis
        total_pages = len(doc)
        complex_pages = sum(1 for p in page_analysis if p['has_complex_graphics'])
        doc.close()
        
        self._log(f"📊 Analysis complete: {total_pages} pages, complex graphics detected on {complex_pages} pages")
        return page_analysis
    
    def _detect_table_heuristic(self, page):
        """Enhanced heuristic to detect tables"""
        text = page.get_text().lower()
        
        # Look for table indicators
        table_indicators = [
            'table', 'column', 'row', 'coefficient', 'std', 'error',
            'regression', 'estimate', 'p-value', 'significant', 'obs',
            '***', '**', '*', '(1)', '(2)', '(3)', '(4)', '(5)',
            'dependent variable', 'independent variable', 'control',
            'robust', 'clustered', 'fixed effects', 'random effects'
        ]
        
        # Count numeric patterns that suggest tabular data
        numeric_patterns = len(re.findall(r'\b\d+\.\d+\b', text))
        parenthetical_numbers = len(re.findall(r'\(\d+\.\d+\)', text))
        
        score = sum(1 for indicator in table_indicators if indicator in text)
        score += min(numeric_patterns // 5, 5)  # Cap numeric score
        score += min(parenthetical_numbers // 3, 3)
        
        return score >= 3
    
    def _detect_figure_heuristic(self, page, images, drawings):
        """Enhanced heuristic to detect figures with caption-based detection"""
        text = page.get_text()
        text_lower = text.lower()
        
        # Look for figure captions at start of lines (more precise than general text search)
        lines = text.split('\n')
        caption_patterns = [
            r'^\s*figure\s+\d+',
            r'^\s*fig\.\s+\d+',
            r'^\s*panel\s+[a-z]',
            r'^\s*table\s+\d+',  # Sometimes figures are mislabeled as tables
        ]
        
        caption_score = 0
        for line in lines:
            line_lower = line.lower().strip()
            for pattern in caption_patterns:
                if re.match(pattern, line_lower):
                    caption_score += 2  # Strong indicator of actual figure
                    break
        
        # General figure-related content indicators
        content_indicators = [
            'chart', 'graph', 'plot', 'distribution', 'histogram', 
            'scatter', 'correlation', 'trend', 'pattern'
        ]
        
        content_score = sum(1 for indicator in content_indicators if indicator in text_lower)
        
        # Images and drawings contribute but with lower weight
        image_score = min(len(images), 2)  # Cap at 2 points for images
        drawing_score = min(len(drawings) // 15, 2)  # Reduced weight for drawings
        
        total_score = caption_score + content_score + image_score + drawing_score
        
        return total_score >= 3
    
    def extract_tables_tabula(self):
        """Extract tables using Tabula-py (best for form-based tables)"""
        self._log("📋 Extracting tables with Tabula...")
        
        try:
            # Use different parameter names for tabula
            strategies = [
                {'lattice': True, 'multiple_tables': True},
                {'stream': True, 'multiple_tables': True},
                {'guess': True, 'multiple_tables': True}
            ]
            
            tabula_results = []
            
            for i, strategy in enumerate(strategies):
                try:
                    method_name = ['lattice', 'stream', 'guess'][i]
                    self._log(f"   🔄 Trying {method_name} method...")
                    
                    tables = tabula.read_pdf(
                        self.pdf_path,
                        pages='all',
                        **strategy
                    )
                    
                    if tables:
                        method_prefix = f"tabula_{method_name}"
                        for j, table in enumerate(tables):
                            if not table.empty and len(table) > 1:  # Skip empty or single-row tables
                                filename = f"{method_prefix}_table_{j+1}.csv"
                                filepath = f"{self.output_dir}/tables/{filename}"
                                table.to_csv(filepath, index=False)
                                
                                tabula_results.append({
                                    'method': method_prefix,
                                    'table_id': j+1,
                                    'filename': filename,
                                    'filepath': filepath,
                                    'shape': table.shape,
                                    'columns': list(table.columns)
                                })
                                
                        self._log(f"   ✅ Found {len(tables)} tables with {method_name}")
                
                except Exception as e:
                    self._log(f"   ❌ {method_name} failed: {str(e)[:100]}")
                    continue
            
            if tabula_results:
                self.results['extraction_methods'].append('tabula')
            return tabula_results
            
        except Exception as e:
            self._log(f"❌ Tabula extraction failed: {e}")
            return []
    
    def extract_tables_camelot(self):
        """Extract tables using Camelot (good for complex layouts)"""
        self._log("🐪 Extracting tables with Camelot...")
        
        try:
            camelot_results = []
            
            # Try different extraction methods
            methods = ['lattice', 'stream']
            
            for method in methods:
                try:
                    self._log(f"   🔄 Trying {method} method...")
                    
                    tables = camelot.read_pdf(
                        self.pdf_path,
                        pages='all',
                        flavor=method,
                        suppress_stdout=True
                    )
                    
                    if tables:
                        method_name = f"camelot_{method}"
                        for i, table in enumerate(tables):
                            if not table.df.empty and len(table.df) > 1:
                                filename = f"{method_name}_table_{i+1}.csv"
                                filepath = f"{self.output_dir}/tables/{filename}"
                                table.to_csv(filepath)
                                
                                camelot_results.append({
                                    'method': method_name,
                                    'table_id': i+1,
                                    'filename': filename,
                                    'filepath': filepath,
                                    'shape': table.df.shape,
                                    'accuracy': getattr(table, 'accuracy', 0),
                                    'whitespace': getattr(table, 'whitespace', 0)
                                })
                        
                        self._log(f"   ✅ Found {len(tables)} tables with {method}")
                
                except Exception as e:
                    self._log(f"   ❌ {method} failed: {str(e)[:100]}")
                    continue
            
            if camelot_results:
                self.results['extraction_methods'].append('camelot')
            return camelot_results
            
        except Exception as e:
            self._log(f"❌ Camelot extraction failed: {e}")
            return []
    
    def extract_tables_pdfplumber(self):
        """Extract tables using pdfplumber (good for precise text extraction)"""
        self._log("🔍 Extracting tables with pdfplumber...")
        
        try:
            pdfplumber_results = []
            
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    
                    if tables:
                        for table_num, table in enumerate(tables):
                            if table and len(table) > 1:  # Skip empty or single-row tables
                                # Convert to DataFrame
                                df = pd.DataFrame(table[1:], columns=table[0] if table[0] else None)
                                
                                if not df.empty:
                                    filename = f"pdfplumber_page_{page_num+1}_table_{table_num+1}.csv"
                                    filepath = f"{self.output_dir}/tables/{filename}"
                                    df.to_csv(filepath, index=False)
                                    
                                    pdfplumber_results.append({
                                        'method': 'pdfplumber',
                                        'page': page_num + 1,
                                        'table_id': table_num + 1,
                                        'filename': filename,
                                        'filepath': filepath,
                                        'shape': df.shape
                                    })
            
            self._log(f"   ✅ Found {len(pdfplumber_results)} tables with pdfplumber")
            if pdfplumber_results:
                self.results['extraction_methods'].append('pdfplumber')
            return pdfplumber_results
            
        except Exception as e:
            self._log(f"❌ pdfplumber extraction failed: {e}")
            return []
    
    def extract_figures_advanced(self):
        """Extract figures using advanced layer-aware methods"""
        self._log("🖼️ Extracting figures with advanced methods...")
        
        try:
            figures_results = []
            doc = fitz.open(self.pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Method 1: Skip SVG extraction (not needed for this application)
                # SVG files are skipped to save space and processing time
                
                # Method 2: High-resolution page rendering
                if self.results['page_analysis'][page_num]['likely_has_figure']:
                    # Render at high resolution
                    mat = fitz.Matrix(3.0, 3.0)  # 3x scaling for high quality
                    pix = page.get_pixmap(matrix=mat)
                    
                    img_filename = f"figure_page_{page_num+1}_highres.png"
                    img_filepath = f"{self.output_dir}/figures/{img_filename}"
                    pix.save(img_filepath)
                    
                    figures_results.append({
                        'method': 'high_res_render',
                        'page': page_num + 1,
                        'filename': img_filename,
                        'filepath': img_filepath,
                        'type': 'raster',
                        'resolution': '3x'
                    })
                
                # Method 3: Extract embedded images with metadata
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_filename = f"embedded_page_{page_num+1}_img_{img_index+1}.{base_image['ext']}"
                        image_filepath = f"{self.output_dir}/figures/{image_filename}"
                        
                        with open(image_filepath, "wb") as img_file:
                            img_file.write(image_bytes)
                        
                        figures_results.append({
                            'method': 'embedded_extraction',
                            'page': page_num + 1,
                            'filename': image_filename,
                            'filepath': image_filepath,
                            'type': 'embedded',
                            'colorspace': base_image.get('colorspace', 'unknown'),
                            'width': base_image.get('width', 0),
                            'height': base_image.get('height', 0)
                        })
                        
                    except Exception as e:
                        continue
            
            doc.close()
            self._log(f"   ✅ Extracted {len(figures_results)} figure files")
            if figures_results:
                self.results['extraction_methods'].append('advanced_figures')
            return figures_results
            
        except Exception as e:
            self._log(f"❌ Advanced figure extraction failed: {e}")
            return []
    
    def _table_to_markdown(self, csv_path, max_rows=10):
        """Convert CSV table to Markdown table format (first max_rows rows)"""
        try:
            df = pd.read_csv(csv_path)
            if df.empty:
                return "*Empty table*\n"
                
            # Limit to first max_rows
            df_preview = df.head(max_rows)
            
            # Clean up column names and data for markdown
            df_preview.columns = [str(col).strip() if col else f"Col_{i}" for i, col in enumerate(df_preview.columns)]
            
            # Convert to markdown
            markdown = df_preview.to_markdown(index=False, tablefmt='github')
            
            if len(df) > max_rows:
                markdown += f"\n\n*Showing first {max_rows} of {len(df)} rows*\n"
                
            return markdown + "\n"
            
        except Exception as e:
            return f"*Error reading table: {str(e)}*\n"
    
    def run_full_extraction(self):
        """Run the complete extraction pipeline"""
        self._log("🚀 Starting advanced PDF extraction pipeline...", force=True)
        self._log(f"📄 Processing: {self.pdf_path}", force=True)
        
        # Step 1: Analyze structure
        self.analyze_pdf_structure()
        
        # Step 2: Extract tables using multiple methods
        self._log("\n" + "="*50, force=True)
        self._log("TABLE EXTRACTION", force=True)
        self._log("="*50, force=True)
        
        tabula_tables = self.extract_tables_tabula()
        camelot_tables = self.extract_tables_camelot()
        pdfplumber_tables = self.extract_tables_pdfplumber()
        
        all_tables = tabula_tables + camelot_tables + pdfplumber_tables
        self.results['tables'] = all_tables
        
        # Step 3: Extract figures
        self._log("\n" + "="*50, force=True)
        self._log("FIGURE EXTRACTION", force=True)
        self._log("="*50, force=True)
        
        figures = self.extract_figures_advanced()
        self.results['figures'] = figures
        
        # Step 4: Generate comprehensive report
        self.generate_report()
        
        self._log("\n" + "="*50, force=True)
        self._log("EXTRACTION COMPLETE!", force=True)
        self._log("="*50, force=True)
        self._log(f"📋 Tables found: {len(all_tables)}", force=True)
        self._log(f"🖼️ Figures found: {len(figures)}", force=True)
        self._log(f"📁 Output directory: {self.output_dir}", force=True)
        
        return self.results
    
    def generate_report(self):
        """Generate a comprehensive extraction report with previews"""
        report_path = f"{self.output_dir}/extraction_report.json"
        
        # Create human-readable summary
        summary = {
            'pdf_file': self.pdf_path,
            'extraction_timestamp': pd.Timestamp.now().isoformat(),
            'total_pages': self.results['metadata']['total_pages'],
            'methods_used': self.results['extraction_methods'],
            'extraction_summary': {
                'tables_found': len(self.results['tables']),
                'figures_found': len(self.results['figures']),
                'pages_with_tables': len([p for p in self.results['page_analysis'] if p['likely_has_table']]),
                'pages_with_figures': len([p for p in self.results['page_analysis'] if p['likely_has_figure']]),
            },
            'table_methods': {
                method: len([t for t in self.results['tables'] if method in t.get('method', '')])
                for method in ['tabula', 'camelot', 'pdfplumber']
            },
            'figure_methods': {
                method: len([f for f in self.results['figures'] if method in f.get('method', '')])
                for method in ['high_res_render', 'embedded_extraction']
            }
        }
        
        # Save detailed results
        with open(report_path, 'w') as f:
            json.dump({
                'summary': summary,
                'detailed_results': self.results
            }, f, indent=2, default=str)
        
        # Create enhanced markdown report
        md_report_path = f"{self.output_dir}/EXTRACTION_REPORT.md"
        with open(md_report_path, 'w') as f:
            f.write(f"# Advanced PDF Extraction Report\n\n")
            f.write(f"**File:** `{self.pdf_path}`  \n")
            f.write(f"**Output Directory:** `{self.output_dir}/`  \n")
            f.write(f"**Extracted:** {summary['extraction_timestamp']}  \n")
            f.write(f"**Total Pages:** {summary['total_pages']}  \n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Tables Found:** {summary['extraction_summary']['tables_found']}\n")
            f.write(f"- **Figures Found:** {summary['extraction_summary']['figures_found']}\n")
            f.write(f"- **Pages with Tables:** {summary['extraction_summary']['pages_with_tables']}\n")
            f.write(f"- **Pages with Figures:** {summary['extraction_summary']['pages_with_figures']}\n\n")
            
            f.write("## Methods Used\n\n")
            f.write("### Table Extraction\n")
            for method, count in summary['table_methods'].items():
                if count > 0:
                    f.write(f"- **{method}:** {count} tables\n")
            
            f.write("\n### Figure Extraction\n")
            for method, count in summary['figure_methods'].items():
                if count > 0:
                    f.write(f"- **{method}:** {count} figures\n")
            
            # Add figures section with image displays
            f.write("\n## Extracted Figures\n\n")
            png_figures = [fig for fig in self.results['figures'] if fig['filename'].endswith('.png')]
            if png_figures:
                for figure in png_figures:
                    f.write(f"### {figure['filename']} ({figure['method']})\n")
                    f.write(f"**Page:** {figure['page']} | **Type:** {figure['type']}\n\n")
                    # Use relative path for markdown image display
                    rel_path = f"figures/{figure['filename']}"
                    f.write(f"![{figure['filename']}]({rel_path})\n\n")
            else:
                f.write("*No PNG figures extracted*\n\n")
            
            # Add tables section with previews
            f.write("\n## Extracted Tables\n\n")
            if self.results['tables']:
                for i, table in enumerate(self.results['tables'], 1):
                    f.write(f"### Table {i}: {table['filename']} ({table['method']})\n")
                    f.write(f"**Shape:** {table['shape']} | **Path:** `tables/{table['filename']}`\n\n")
                    
                    # Add table preview
                    f.write("#### Preview (First 10 rows):\n\n")
                    table_md = self._table_to_markdown(table['filepath'], max_rows=10)
                    f.write(table_md)
                    f.write("\n---\n\n")
            else:
                f.write("*No tables extracted*\n\n")
            
            # Add file listing
            f.write("\n## All Generated Files\n\n")
            f.write("### Figures\n")
            for figure in self.results['figures']:
                f.write(f"- `figures/{figure['filename']}` ({figure['method']})\n")
            
            f.write("\n### Tables\n")
            for table in self.results['tables']:
                f.write(f"- `tables/{table['filename']}` ({table['method']})\n")
        
        self._log(f"📊 Reports saved: {report_path} and {md_report_path}")

def create_argument_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="Advanced PDF Content Extractor - Extract tables and figures from complex PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf                    # Extract to extracted_content_document/
  %(prog)s PDF_Proof.PDF --verbose        # Extract with detailed output
  %(prog)s report.pdf -o custom_output     # Extract to custom_output/
  
Requirements:
  - Python 3.12+
  - Java Runtime Environment (for tabula)
  - Virtual environment with required packages
  
Output Structure:
  extracted_content_FILENAME/
  ├── tables/                 # CSV files with extracted tables
  ├── figures/                # PNG/SVG files with extracted figures
  ├── raw_data/               # Intermediate processing files
  ├── EXTRACTION_REPORT.md    # Comprehensive report with previews
  └── extraction_report.json  # Machine-readable results

Installation:
  1. python3.12 -m venv pdf_extraction_env
  2. source pdf_extraction_env/bin/activate
  3. pip install -r requirements-pdfextractor.txt
  
  Alternative (manual install):
  pip install tabula-py camelot-py[cv] PyMuPDF pdfplumber pandas numpy Pillow opencv-python

Dependencies Check:
  If you get import errors, ensure all packages are installed:
  • tabula-py (requires Java Runtime)
  • camelot-py[cv] (includes OpenCV)
  • PyMuPDF (PDF processing)
  • pdfplumber (text extraction)
  • pandas, numpy (data processing)
  • Pillow (image processing)
        """
    )
    
    parser.add_argument(
        'pdf_file',
        help='Path to the PDF file to extract content from'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_dir',
        help='Output directory (default: extracted_content_FILENAME based on PDF name)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output showing detailed progress'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Advanced PDF Extractor 2.0'
    )
    
    return parser

def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Import dependencies only after parsing arguments (allows --help to work without imports)
    _import_dependencies()
    
    # Validate input file
    if not os.path.exists(args.pdf_file):
        print(f"❌ Error: File '{args.pdf_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    if not args.pdf_file.lower().endswith('.pdf'):
        print(f"❌ Error: '{args.pdf_file}' is not a PDF file", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Run extraction
        extractor = AdvancedPDFExtractor(args.pdf_file, args.output_dir, args.verbose)
        results = extractor.run_full_extraction()
        
        print(f"\n✅ Extraction completed successfully!")
        print(f"📁 Results saved to: {extractor.output_dir}/")
        print(f"📋 View detailed report: {extractor.output_dir}/EXTRACTION_REPORT.md")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Extraction cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Extraction failed: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())