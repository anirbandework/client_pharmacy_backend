import pdfplumber

pdf_path = 'modules/invoice_analyzer/SW000106.pdf'
with pdfplumber.open(pdf_path) as pdf:
    text = ""
    for page in pdf.pages:
        text += page.extract_text() or ""

print(text)
