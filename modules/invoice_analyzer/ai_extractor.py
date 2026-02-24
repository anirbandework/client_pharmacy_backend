import pdfplumber
import json
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Using fallback extraction.")

class AIInvoiceExtractor:
    """AI-powered invoice extraction that works with any PDF format"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                # Use Gemini 2.5 Flash (fastest and most cost-effective)
                self.model = genai.GenerativeModel('models/gemini-2.5-flash')
                logger.info("✅ Gemini AI configured successfully with gemini-2.5-flash - AI extraction enabled")
            except Exception as e:
                logger.error(f"❌ Failed to configure Gemini AI: {e}")
                self.model = None
        else:
            self.model = None
            if not self.api_key:
                logger.warning("⚠️ No Gemini API key found - using fallback extraction")
            if not GENAI_AVAILABLE:
                logger.warning("⚠️ google-generativeai not installed - using fallback extraction")
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract invoice data using AI"""
        
        # Extract text from PDF
        text = self._extract_text(pdf_path)
        
        if not text:
            raise ValueError("No text extracted from PDF")
        
        # Use AI to extract structured data
        if self.model:
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
      "manufacturer": "Mfg code or null",
      "hsn_code": "HSN code",
      "product_name": "product name",
      "batch_number": "batch",
      "quantity": number,
      "package": "Pkg value like '10 X 6' or null",
      "expiry_date": "MM/YYYY",
      "mrp": "exact MRP text like '69.00/STRIP' or '299.00/STRIP' or null",
      "free_quantity": 0,
      "unit_price": number,
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
- IMPORTANT: Mfg and HSN are SEPARATE fields:
  * Mfg (manufacturer) is typically 4 letters (e.g., "ELEG", "BIOD")
  * HSN code is typically 8 digits (e.g., "30042064", "30049099")
  * Do NOT concatenate them - keep them separate
- Extract Pkg (package) column if present (e.g., "10 X 6", "10 x 10")
- Extract MRP column if present - keep EXACT text as shown (e.g., "69.00/STRIP", "299.00/STRIP", "422.20/BOTTLE")
- For expiry_date: Use the EXACT format from the invoice
  * If invoice shows MM/YYYY (e.g., "11/2026"), use "11/2026"
  * If invoice shows DD/MM/YYYY (e.g., "15/11/2026"), use "15/11/2026"
  * Keep the format as-is from the source document
- Use exact amounts from the invoice
- Calculate total_gst as sum of all CGST + SGST + IGST
- If CGST/SGST are present, IGST should be 0
- taxable_amount for items = amount before tax
- total_amount for items = amount + CGST + SGST

Invoice:
{text}
"""
        
        try:
            response = self.model.generate_content(prompt)
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
        product_name = None
        
        for i, line in enumerate(lines):
            if re.search(r'H\.?S\.?N|Product Name', line, re.IGNORECASE):
                in_items = True
                continue
            
            # Break only when we hit the Rupees line followed by Tax % table
            if in_items and re.search(r'^Rupees\s*:', line, re.IGNORECASE):
                break
            
            if not in_items or not line.strip():
                continue
            
            # Check if line has MFG+HSN pattern (anywhere in line, with optional space)
            mfg_hsn_match = re.search(r'([A-Z]{4})\s?(\d{8})', line)
            
            if mfg_hsn_match and re.search(r'\d{2}/\d{4}', line):
                # This line has data
                hsn_code = mfg_hsn_match.group(2)
                mfg_code = mfg_hsn_match.group(1)
                
                # Extract product name: it's between HSN and batch number
                # Find position after HSN
                hsn_end_pos = line.find(hsn_code) + len(hsn_code)
                after_hsn = line[hsn_end_pos:].strip()
                
                # Extract batch and expiry to know where product name ends
                batch_match = re.search(r'\b([A-Z0-9-]{4,15})\b\s+\d+\s+\d{2}/\d{4}', after_hsn)
                if batch_match:
                    # Product name is everything before the batch
                    batch_start = after_hsn.find(batch_match.group(1))
                    extracted_name = after_hsn[:batch_start].strip()
                    if extracted_name:
                        product_name = extracted_name
                    elif product_name and re.search(r'[A-Z]{3,}', product_name):
                        # Use previous line if current line has no product name
                        pass
                    else:
                        product_name = "Unknown Product"
                else:
                    # Fallback: use previous line if it looks like a product name
                    if product_name and re.search(r'[A-Z]{3,}', product_name):
                        pass  # Keep stored product_name
                    else:
                        product_name = "Unknown Product"
                
                # Extract batch
                batch_match = re.search(r'\b([A-Z0-9]{5,10})\b', line)
                batch = batch_match.group(1) if batch_match and batch_match.group(1) != hsn_code else None
                
                # Extract quantity (number before package or expiry)
                qty_match = re.search(r'\b(\d+)\s+(?:(\d+\s*[xX]\s*\d+)|\d{2}/\d{4})', line)
                quantity = float(qty_match.group(1)) if qty_match else 1.0
                
                # Extract package (e.g., "10 X 6" or "10 x 10")
                pkg_match = re.search(r'(\d+\s*[xX]\s*\d+)', line)
                package = pkg_match.group(1) if pkg_match else None
                
                # Extract MRP (e.g., "69.00/STRIP" or "299.00/STRIP")
                # Look for pattern: number/UNIT but NOT if preceded by expiry date pattern
                mrp_match = re.search(r'(?<!\d{2}/\d{4}\s)([\d.]+/(?:STRIP|BOTTLE|PACK|TUBE|BOX))', line)
                mrp = mrp_match.group(1) if mrp_match else None
                
                # Extract expiry (MM/YYYY format)
                expiry_match = re.search(r'(\d{2}/\d{4})', line)
                expiry = expiry_match.group(1) if expiry_match else None
                
                # Fix concatenated numbers
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
                        "manufacturer": mfg_code,
                        "hsn_code": hsn_code,
                        "product_name": product_name,
                        "batch_number": batch,
                        "quantity": quantity,
                        "package": package,
                        "expiry_date": expiry,
                        "mrp": mrp,
                        "free_quantity": 0,
                        "unit_price": rate / quantity if quantity > 0 else rate,
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
                    product_name = None
            else:
                # Store as potential product name
                if re.search(r'[A-Z]{3,}', line):
                    product_name = line.strip()
        
        return items
