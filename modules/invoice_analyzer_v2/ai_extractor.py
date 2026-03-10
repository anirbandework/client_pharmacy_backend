import pdfplumber
import json
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not installed. Using fallback extraction.")

class AIInvoiceExtractor:
    """AI-powered invoice extraction that works with any PDF format"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key and GENAI_AVAILABLE:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("✅ Gemini AI configured successfully - AI extraction enabled")
            except Exception as e:
                logger.error(f"❌ Failed to configure Gemini AI: {e}")
                self.client = None
        else:
            self.client = None
            if not self.api_key:
                logger.warning("⚠️ No Gemini API key found - using fallback extraction")
            if not GENAI_AVAILABLE:
                logger.warning("⚠️ google-genai not installed - using fallback extraction")
    
    def validate_document_format(self, text: str, file_type: str = "PDF") -> Dict[str, Any]:
        """Use AI to validate document format and provide detailed feedback"""
        
        if not self.client:
            return {
                "is_valid": False,
                "error": "AI validation not available. Please ensure document has: Invoice Number, Date, Supplier Name, Items with Product Name, Batch, Quantity, Price, GST details."
            }
        
        logger.info(f"🔍 Validating {file_type} format with AI...")
        
        # For Excel files, be more lenient with NaN values in header fields
        excel_note = ""
        if file_type == "Excel":
            excel_note = """
IMPORTANT for Excel files:
- Invoice header fields (Invoice_Number, Invoice_Date, Supplier_Name) appear ONLY in the first row
- Subsequent item rows will have NaN/empty values for these fields - this is NORMAL and VALID
- Do NOT flag NaN values in header fields for rows after the first row as an error
- Focus validation on: presence of header fields in first row, and item-level fields in all rows
"""
        
        prompt = f"""
Analyze this invoice document and check if it has the required format for data extraction.
{excel_note}

Required fields:
1. Invoice Header: Invoice Number, Invoice Date, At least ONE supplier field (name, address, GSTIN, DL numbers, or phone)
2. Item Details (per product row): Product Name, Batch Number, Quantity, Unit Price, GST details

Return ONLY valid JSON (no markdown):
{{
  "is_valid": true/false,
  "can_extract_anyway": true/false (true if basic fields present but has format issues),
  "missing_fields": ["list of missing required fields"],
  "format_issues": ["list of format problems"],
  "suggestions": ["detailed suggestions to fix the document"],
  "detected_fields": {{
    "invoice_number": "found value or null",
    "invoice_date": "found value or null",
    "supplier_name": "found value or null",
    "supplier_address": "found value or null",
    "supplier_gstin": "found value or null",
    "supplier_dl_numbers": "found value or null",
    "supplier_phone": "found value or null",
    "has_any_supplier_field": true/false,
    "items_count": number of items found,
    "has_product_names": true/false,
    "has_batch_numbers": true/false,
    "has_quantities": true/false,
    "has_prices": true/false,
    "has_gst_details": true/false
  }}
}}

Rules:
- Set is_valid=true only if document is perfectly formatted
- Set can_extract_anyway=true if invoice_number, invoice_date, at least one supplier field, and items are present (even with format issues)
- Set can_extract_anyway=false if critical fields are missing
- Set has_any_supplier_field=true if ANY of: supplier_name, supplier_address, supplier_gstin, supplier_dl_numbers, or supplier_phone is present

Document:
{text[:3000]}
"""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            result_text = response.text.strip()
            
            if result_text.startswith('```'):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else result_text
                if result_text.startswith('json'):
                    result_text = result_text[4:].strip()
            
            validation = json.loads(result_text)
            logger.info(f"✅ Format validation complete: is_valid={validation.get('is_valid')}, can_extract_anyway={validation.get('can_extract_anyway')}")
            return validation
            
        except Exception as e:
            logger.error(f"❌ Format validation failed: {e}")
            return {
                "is_valid": False,
                "can_extract_anyway": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract invoice data using AI"""
        
        # Extract text from PDF
        text = self._extract_text(pdf_path)
        
        if not text:
            raise ValueError("No text extracted from PDF")
        
        # Use AI to extract structured data
        if self.client:
            return self._ai_extract(text)
        else:
            return self._fallback_extract(text)
    
    def _extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise ValueError(f"Failed to extract PDF: {str(e)}")
    
    def _ai_extract(self, text: str) -> Dict[str, Any]:
        """Use AI to extract invoice data"""
        
        logger.info("🤖 Using Gemini AI for invoice extraction...")
        
        prompt = f"""
Extract ALL data from this invoice. Return ONLY valid JSON (no markdown):

{{
  "invoice_number": "complete invoice number",
  "invoice_date": "DD/MM/YYYY",
  "due_date": "DD/MM/YYYY or null",
  "supplier_name": "supplier/vendor name",
  "supplier_address": "full address or null",
  "supplier_gstin": "15 digit GSTIN or null",
  "supplier_dl_numbers": "all DL numbers comma separated or null",
  "supplier_phone": "phone number or null",
  "items": [
    {{
      "composition": "generic/salt name (e.g., Paracetamol 500mg) or null",
      "manufacturer": "Mfg code (e.g., CIPLA, SUN) or null",
      "hsn_code": "HSN code",
      "product_name": "brand/product name",
      "batch_number": "batch",
      "quantity": number,
      "package": "Pkg value like '10 X 6' or null",
      "unit": "unit type (Box, Strip, Bottle, etc.) or null",
      "manufacturing_date": "MM/YYYY or DD/MM/YYYY or null",
      "expiry_date": "MM/YYYY or DD/MM/YYYY",
      "mrp": "exact MRP text like '69.00/STRIP' or '299.00/STRIP' or null",
      "selling_price": 0,
      "profit_margin": 0,
      "discount_on_purchase": 0,
      "discount_on_sales": 0,
      "free_quantity": 0,
      "unit_price": number,
      "before_discount": 0,
      "discount_percent": 0,
      "discount_amount": 0,
      "taxable_amount": number,
      "cgst_percent": number,
      "cgst_amount": number,
      "sgst_percent": number,
      "sgst_amount": number,
      "igst_percent": 0,
      "igst_amount": 0,
      "total_amount": number
    }}
  ],
  "gross_amount": number,
  "discount_amount": number,
  "taxable_amount": number,
  "total_gst": number,
  "round_off": number,
  "net_amount": number
}}

Rules:
- Extract ALL items from the invoice
- IMPORTANT: Separate fields properly:
  * composition = generic/salt name (e.g., "Paracetamol 500mg", "Telmisartan 40")
  * product_name = brand name (e.g., "Dolo 650", "Telma")
  * manufacturer = Mfg code, typically 4 letters (e.g., "CIPLA", "SUN", "ELEG")
  * hsn_code = HSN code, typically 8 digits (e.g., "30049099", "30042064")
  * Do NOT concatenate manufacturer and HSN - keep them separate
- Extract package (e.g., "10 X 6", "10 x 10") if present
- Extract unit type (Box, Strip, Bottle, Vial, Cartridge, Piece, Tablets, Capsules, Sachet, Inhaler, gm, kg, ml, L) if present
- Extract manufacturing_date if present (MM/YYYY or DD/MM/YYYY format)
- Extract MRP - keep EXACT text as shown (e.g., "69.00/STRIP", "299.00/STRIP", "422.20/BOTTLE")
- For expiry_date: Use the EXACT format from the invoice
  * If invoice shows MM/YYYY (e.g., "11/2026"), use "11/2026"
  * If invoice shows DD/MM/YYYY (e.g., "15/11/2026"), use "15/11/2026"
- Extract selling_price, profit_margin, discount_on_purchase, discount_on_sales if present
- Use exact amounts from the invoice
- Calculate before_discount = quantity × unit_price (if not explicitly shown)
- Calculate total_gst as sum of all CGST + SGST + IGST
- If CGST/SGST are present, IGST should be 0
- taxable_amount for items = amount before tax
- total_amount for items = amount + CGST + SGST

Invoice:
{text}
"""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            result_text = response.text.strip()
            
            if result_text.startswith('```'):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else result_text
                if result_text.startswith('json'):
                    result_text = result_text[4:].strip()
            
            data = json.loads(result_text)
            
            # Validate and fix data
            if not data.get("items"):
                logger.warning("⚠️ AI returned no items, using fallback")
                return self._fallback_extract(text)
            
            logger.info(f"✅ AI extraction successful - extracted {len(data.get('items', []))} items")
            
            # Fix common extraction errors
            for item in data.get("items", []):
                # Fix concatenated Mfg+HSN (e.g., "ELEG30042064" should be Mfg="ELEG", HSN="30042064")
                if item.get("manufacturer") and len(item["manufacturer"]) > 4:
                    # Check if it's Mfg+HSN concatenated
                    import re
                    match = re.match(r'^([A-Z]{4})(\d{8})$', item["manufacturer"])
                    if match:
                        item["manufacturer"] = match.group(1)
                        if not item.get("hsn_code") or item["hsn_code"] == "-":
                            item["hsn_code"] = match.group(2)
                
                # Auto-calculate before_discount if missing
                if item.get("before_discount", 0) == 0 and item.get("unit_price", 0) > 0:
                    item["before_discount"] = item.get("quantity", 0) * item.get("unit_price", 0)
                
                # Auto-calculate taxable_amount if missing
                if item.get("taxable_amount", 0) == 0:
                    if item.get("before_discount", 0) > 0:
                        item["taxable_amount"] = item.get("before_discount", 0) - item.get("discount_amount", 0)
                    else:
                        item["taxable_amount"] = item.get("quantity", 0) * item.get("unit_price", 0)
            
            # Ensure total_gst is calculated
            if data.get("total_gst", 0) == 0:
                cgst = data.get("cgst_amount", 0) or sum(item.get("cgst_amount", 0) for item in data.get("items", []))
                sgst = data.get("sgst_amount", 0) or sum(item.get("sgst_amount", 0) for item in data.get("items", []))
                igst = data.get("igst_amount", 0) or sum(item.get("igst_amount", 0) for item in data.get("items", []))
                data["total_gst"] = cgst + sgst + igst
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ AI JSON parsing error: {e} - using fallback")
            return self._fallback_extract(text)
        except Exception as e:
            logger.error(f"❌ AI extraction failed: {e} - using fallback")
            return self._fallback_extract(text)
    
    def _fallback_extract(self, text: str) -> Dict[str, Any]:
        """Enhanced fallback extraction"""
        import re
        from datetime import datetime
        
        logger.info("🔧 Using fallback regex extraction...")
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        data = {
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "supplier_name": None,
            "supplier_address": None,
            "supplier_gstin": None,
            "supplier_dl_numbers": None,
            "supplier_phone": None,
            "items": [],
            "gross_amount": 0.0,
            "discount_amount": 0.0,
            "taxable_amount": 0.0,
            "total_gst": 0.0,
            "round_off": 0.0,
            "net_amount": 0.0
        }
        
        # Extract supplier name (usually first non-empty line after "Sale Invoice" or similar)
        for i, line in enumerate(lines[:15]):
            if any(x in line.lower() for x in ['sale invoice', 'purchase invoice', 'tax invoice']):
                if i + 1 < len(lines):
                    data["supplier_name"] = lines[i + 1]
                break
        
        # Extract invoice number
        inv_match = re.search(r'Invoice No\s*:\s*([A-Z0-9/-]+)', text, re.IGNORECASE)
        if inv_match:
            inv_num = inv_match.group(1).strip()
            # Check if there's a continuation on next line
            inv_idx = text.find(inv_match.group(0))
            if inv_idx > 0:
                remaining = text[inv_idx:inv_idx+200]
                next_line_match = re.search(r'Invoice No\s*:\s*([A-Z0-9/-]+)\s*\.?\s*(\d+)', remaining, re.IGNORECASE)
                if next_line_match and next_line_match.group(2):
                    inv_num = inv_match.group(1) + next_line_match.group(2)
            data["invoice_number"] = inv_num
        
        # Extract dates
        date_matches = re.findall(r'Date\s*:\s*(\d{2}/\d{2}/\d{4})', text)
        if date_matches:
            data["invoice_date"] = date_matches[0]
        
        due_match = re.search(r'Due Date\s*:\s*(\d{2}/\d{2}/\d{4})', text)
        if due_match:
            data["due_date"] = due_match.group(1)
        
        # Extract GSTIN
        gstin_match = re.search(r'GSTIN\s*(?:No)?\s*:\s*([A-Z0-9]{15})', text, re.IGNORECASE)
        if gstin_match:
            data["supplier_gstin"] = gstin_match.group(1)
        
        # Extract DL numbers
        # Pattern 1: DL No. :WLF20B2025TR000022, WLF21B2025TR000021
        dl_match = re.search(r'DL\s*No\.?\s*:\s*([A-Z0-9,\s-]+?)(?:Food|E-MAIL|\n\n)', text, re.IGNORECASE)
        if dl_match:
            dl_text = dl_match.group(1)
            dls = [d.strip() for d in re.split(r'[,\s]+', dl_text) if d.strip() and len(d.strip()) > 5]
            if dls:
                data["supplier_dl_numbers"] = ', '.join(dls)
        else:
            # Pattern 2: DL 1 : xxx , DL 2 : yyy
            dl_matches = re.findall(r'DL\s*\d+\s*:\s*([A-Z0-9-]+)', text, re.IGNORECASE)
            if dl_matches:
                data["supplier_dl_numbers"] = ', '.join(dl_matches)
        
        # Extract phone
        phone_match = re.search(r'Ph\s*(?:No)?\s*[:\.]?\s*(\d{10})', text, re.IGNORECASE)
        if phone_match:
            data["supplier_phone"] = phone_match.group(1)
        else:
            # Try alternative pattern
            phone_match = re.search(r'\b(\d{10})\b', text[:500])  # Look in first 500 chars
            if phone_match:
                data["supplier_phone"] = phone_match.group(1)
        
        # Extract items
        data["items"] = self._extract_items_fallback(text)
        
        # Extract totals
        gross_match = re.search(r'Gross Amount\s*:\s*([\d,]+\.\d+)', text, re.IGNORECASE)
        if gross_match:
            data["gross_amount"] = float(gross_match.group(1).replace(',', ''))
        
        disc_match = re.search(r'Discount\s*:\s*([\d,]+\.\d+)', text, re.IGNORECASE)
        if disc_match:
            data["discount_amount"] = float(disc_match.group(1).replace(',', ''))
        
        tax_match = re.search(r'Taxable Amount\s*:\s*([\d,]+\.\d+)', text, re.IGNORECASE)
        if tax_match:
            data["taxable_amount"] = float(tax_match.group(1).replace(',', ''))
        
        gst_match = re.search(r'GST Amount\s*:\s*([\d,]+\.\d+)', text, re.IGNORECASE)
        if gst_match:
            data["total_gst"] = float(gst_match.group(1).replace(',', ''))
        
        round_match = re.search(r'Round Off\s*:\s*([\d.]+)', text, re.IGNORECASE)
        if round_match:
            data["round_off"] = float(round_match.group(1))
        
        net_match = re.search(r'Net Amount\s*:\s*([\d,]+\.\d+)', text, re.IGNORECASE)
        if net_match:
            data["net_amount"] = float(net_match.group(1).replace(',', ''))
        
        return data
    
    def _extract_items_fallback(self, text: str) -> list:
        """Extract items from invoice text"""
        import re
        items = []
        lines = text.split('\n')
        
        in_items = False
        product_name_buffer = []
        
        for i, line in enumerate(lines):
            if re.search(r'H\.?S\.?N|Product Name', line, re.IGNORECASE):
                in_items = True
                continue
            
            if in_items and re.search(r'^Rupees\s*:', line, re.IGNORECASE):
                break
            
            if not in_items or not line.strip():
                continue
            
            # Check if line has MFG+HSN pattern and expiry date (data line)
            mfg_hsn_match = re.search(r'([A-Z]{4})\s?(\d{8})', line)
            
            if mfg_hsn_match and re.search(r'\d{2}/\d{4}', line):
                hsn_code = mfg_hsn_match.group(2)
                mfg_code = mfg_hsn_match.group(1)
                
                # Try to extract product name from current line first
                hsn_end_pos = line.find(hsn_code) + len(hsn_code)
                after_hsn = line[hsn_end_pos:].strip()
                
                # Find batch number position to extract product name
                batch_match = re.search(r'\b([A-Z0-9-]{4,15})\b\s+\d+', after_hsn)
                product_name = None
                
                if batch_match:
                    batch_start = after_hsn.find(batch_match.group(1))
                    extracted_name = after_hsn[:batch_start].strip()
                    if extracted_name and len(extracted_name) > 2:
                        product_name = extracted_name
                
                # If no product name on current line, use buffered lines
                if not product_name and product_name_buffer:
                    product_name = ' '.join(product_name_buffer).strip()
                
                # Clear buffer after using
                product_name_buffer = []
                
                # Extract batch number
                batch_match = re.search(r'\b([A-Z0-9-]{4,15})\b', after_hsn)
                batch = batch_match.group(1) if batch_match else None
                
                # Extract quantity
                qty_match = re.search(r'\b(\d+)\s+(?:(\d+\s*[xX]\s*\d+)|\d{2}/\d{4})', line)
                quantity = float(qty_match.group(1)) if qty_match else 1.0
                
                # Extract package
                pkg_match = re.search(r'(\d+\s*[xX]\s*\d+|\d+\s*(?:ML|GMS|GM))', line, re.IGNORECASE)
                package = pkg_match.group(1) if pkg_match else None
                
                # Extract MRP
                mrp_match = re.search(r'([\d.]+/(?:STRIP|BOTTLE|PACK|TUBE|BOX|PIECE))', line, re.IGNORECASE)
                mrp = mrp_match.group(1) if mrp_match else None
                
                # Extract expiry
                expiry_match = re.search(r'(\d{2}/\d{4})', line)
                expiry = expiry_match.group(1) if expiry_match else None
                
                # Fix concatenated numbers and extract amounts
                line_fixed = re.sub(r'(\d\.\d{2})(\d)', r'\1 \2', line)
                amounts = [float(a.replace(',', '')) for a in re.findall(r'([\d,]+\.\d+)', line_fixed)]
                
                if len(amounts) >= 7:
                    sgst_amt = amounts[-1]
                    sgst_pct = amounts[-2]
                    cgst_amt = amounts[-3]
                    cgst_pct = amounts[-4]
                    amount = amounts[-5]
                    rate = amounts[-6]
                    
                    items.append({
                        "composition": None,
                        "manufacturer": mfg_code,
                        "hsn_code": hsn_code,
                        "product_name": product_name,
                        "batch_number": batch,
                        "quantity": quantity,
                        "package": package,
                        "unit": None,
                        "manufacturing_date": None,
                        "expiry_date": expiry,
                        "mrp": mrp,
                        "selling_price": 0,
                        "profit_margin": 0,
                        "discount_on_purchase": 0,
                        "discount_on_sales": 0,
                        "free_quantity": 0,
                        "unit_price": rate / quantity if quantity > 0 else rate,
                        "before_discount": 0,
                        "discount_percent": 0,
                        "discount_amount": 0,
                        "taxable_amount": amount,
                        "cgst_percent": cgst_pct,
                        "cgst_amount": cgst_amt,
                        "sgst_percent": sgst_pct,
                        "sgst_amount": sgst_amt,
                        "igst_percent": 0,
                        "igst_amount": 0,
                        "total_amount": amount + cgst_amt + sgst_amt
                    })
            else:
                # Buffer potential product name lines
                clean_line = line.strip()
                if clean_line and re.search(r'[A-Z]', clean_line) and not re.search(r'^\d+$', clean_line):
                    product_name_buffer.append(clean_line)
        
        return items
