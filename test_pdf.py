import pdfplumber
import sys

pdf_path = "/Users/anirbande/Desktop/client backend/modules/invoice_analyzer/SW000106.pdf"

try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}\n")
        print("="*80)
        
        for i, page in enumerate(pdf.pages, 1):
            print(f"\n--- PAGE {i} ---\n")
            text = page.extract_text()
            print(text)
            print("\n" + "="*80)
            
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
