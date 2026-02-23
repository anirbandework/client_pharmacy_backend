import pdfplumber
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PDFExtractionService:
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Extract all text from PDF"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise ValueError(f"Failed to extract PDF: {str(e)}")
    
    @staticmethod
    def parse_invoice_data(text: str) -> Dict[str, Any]:
        """Parse invoice data from extracted text"""
        
        data = {
            "supplier": {},
            "shop": {},
            "invoice": {},
            "items": [],
            "totals": {}
        }
        
        lines = text.split('\n')
        
        # Extract invoice number and dates
        for line in lines:
            if 'Invoice No' in line or 'INVOICE NO' in line:
                match = re.search(r'[A-Z0-9/-]+', line.split(':')[-1])
                if match:
                    data["invoice"]["invoice_number"] = match.group().strip()
            
            if 'Date' in line and 'Invoice' not in line:
                match = re.search(r'\d{2}/\d{2}/\d{4}', line)
                if match:
                    data["invoice"]["invoice_date"] = match.group()
            
            if 'Due Date' in line:
                match = re.search(r'\d{2}/\d{2}/\d{4}', line)
                if match:
                    data["invoice"]["due_date"] = match.group()
        
        # Extract supplier info (first entity in invoice)
        supplier_section = text.split('To :')[0] if 'To :' in text else text[:500]
        
        # Extract GSTIN
        gstin_match = re.search(r'GSTIN[:\s]*([A-Z0-9]{15})', supplier_section)
        if gstin_match:
            data["supplier"]["gstin"] = gstin_match.group(1)
        
        # Extract DL numbers
        dl_matches = re.findall(r'DL[:\s]*([A-Z0-9-,\s]+)', supplier_section)
        if dl_matches:
            data["supplier"]["dl_numbers"] = ', '.join(dl_matches)
        
        # Extract phone
        phone_match = re.search(r'Ph[:\s]*([0-9]{10})', supplier_section)
        if phone_match:
            data["supplier"]["phone"] = phone_match.group(1)
        
        # Extract supplier name (first line usually)
        first_lines = [l.strip() for l in lines[:10] if l.strip()]
        if first_lines:
            data["supplier"]["name"] = first_lines[0]
        
        # Extract shop info (after "To :")
        if 'To :' in text:
            shop_section = text.split('To :')[1].split('Invoice No')[0] if 'Invoice No' in text else text.split('To :')[1][:500]
            
            shop_lines = [l.strip() for l in shop_section.split('\n') if l.strip()]
            if shop_lines:
                data["shop"]["name"] = shop_lines[0]
            
            shop_gstin = re.search(r'GST[:\s]*([A-Z0-9]{15})', shop_section)
            if shop_gstin:
                data["shop"]["gstin"] = shop_gstin.group(1)
        
        # Extract items (table data)
        data["items"] = PDFExtractionService._extract_items(text)
        
        # Extract totals
        data["totals"] = PDFExtractionService._extract_totals(text)
        
        return data
    
    @staticmethod
    def _extract_items(text: str) -> List[Dict[str, Any]]:
        """Extract item details from table"""
        items = []
        lines = text.split('\n')
        
        in_items_section = False
        for i, line in enumerate(lines):
            # Start of items section
            if 'Mfg.' in line and 'H.S.N' in line and 'Product Name' in line:
                in_items_section = True
                continue
            
            # End of items section
            if 'Rupees :' in line or 'Tax %' in line:
                in_items_section = False
                break
            
            if not in_items_section:
                continue
            
            # Skip header repetitions and empty lines
            if not line.strip() or 'Mfg.' in line:
                continue
            
            try:
                # Parse line with pattern: MFG HSN PRODUCT BATCH QTY PKG EXPIRY MRP RATE AMOUNT CGST% CGST_AMT SGST% SGST_AMT
                parts = line.split()
                
                if len(parts) < 10:
                    continue
                
                # Extract manufacturer (first part)
                manufacturer = parts[0] if parts else None
                
                # Extract HSN code (8 digits)
                hsn_code = None
                for part in parts:
                    if part.isdigit() and len(part) == 8:
                        hsn_code = part
                        break
                
                # Extract product name (between HSN and batch)
                product_name = ""
                hsn_idx = -1
                for idx, part in enumerate(parts):
                    if part == hsn_code:
                        hsn_idx = idx
                        break
                
                if hsn_idx > 0:
                    # Product name is between manufacturer and batch
                    product_parts = []
                    for idx in range(hsn_idx + 1, len(parts)):
                        # Stop at batch number (alphanumeric pattern)
                        if re.match(r'^[A-Z0-9-]+$', parts[idx]) and len(parts[idx]) > 4:
                            break
                        product_parts.append(parts[idx])
                    product_name = ' '.join(product_parts)
                
                # Extract batch number
                batch_match = re.search(r'\b([A-Z0-9-]{5,})\b', line)
                batch = batch_match.group(1) if batch_match else None
                
                # Extract quantity (number before 'X' or standalone)
                qty_match = re.search(r'(\d+)\s*[Xx]?\s*(\d+)', line)
                quantity = float(qty_match.group(1)) if qty_match else 1.0
                
                # Extract package info
                pkg_match = re.search(r'(\d+\s*[Xx]\s*\d+)', line)
                package = pkg_match.group(1) if pkg_match else None
                
                # Extract expiry date (MM/YYYY)
                expiry_match = re.search(r'(\d{2}/\d{4})', line)
                expiry = expiry_match.group(1) if expiry_match else None
                
                # Extract MRP (number followed by /STRIP, /BOTTLE, /TUBE, etc)
                mrp_match = re.search(r'([\d,]+\.\d+)/(?:STRIP|BOTTLE|TUBE|PACK|PIECE)', line)
                mrp = float(mrp_match.group(1).replace(',', '')) if mrp_match else None
                
                # Extract amounts (last several numbers in line)
                amounts = re.findall(r'([\d,]+\.\d+)', line)
                if len(amounts) >= 5:
                    rate = float(amounts[-5].replace(',', ''))
                    amount = float(amounts[-4].replace(',', ''))
                    cgst_amt = float(amounts[-2].replace(',', ''))
                    sgst_amt = float(amounts[-1].replace(',', ''))
                else:
                    rate = 0.0
                    amount = 0.0
                    cgst_amt = 0.0
                    sgst_amt = 0.0
                
                # Extract GST percentages
                gst_match = re.search(r'(\d+\.\d+)\s+([\d,]+\.\d+)\s+(\d+\.\d+)\s+([\d,]+\.\d+)$', line)
                if gst_match:
                    cgst_percent = float(gst_match.group(1))
                    sgst_percent = float(gst_match.group(3))
                else:
                    cgst_percent = 6.0  # Default
                    sgst_percent = 6.0
                
                if product_name and hsn_code:
                    items.append({
                        "hsn_code": hsn_code,
                        "product_name": product_name.strip(),
                        "manufacturer": manufacturer,
                        "batch_number": batch,
                        "quantity": quantity,
                        "package_info": package,
                        "expiry_date": expiry,
                        "mrp": mrp,
                        "rate": rate,
                        "amount": amount,
                        "cgst_percent": cgst_percent,
                        "cgst_amount": cgst_amt,
                        "sgst_percent": sgst_percent,
                        "sgst_amount": sgst_amt
                    })
            except Exception as e:
                logger.warning(f"Failed to parse item line: {line[:50]}..., error: {str(e)}")
                continue
        
        return items
    
    @staticmethod
    def _extract_totals(text: str) -> Dict[str, float]:
        """Extract financial totals"""
        totals = {
            "gross_amount": 0.0,
            "discount": 0.0,
            "taxable_amount": 0.0,
            "gst_amount": 0.0,
            "round_off": 0.0,
            "net_amount": 0.0
        }
        
        lines = text.split('\n')
        
        for line in lines:
            if 'Gross Amount' in line:
                match = re.search(r'(\d+,?\d*\.?\d+)', line)
                if match:
                    totals["gross_amount"] = float(match.group(1).replace(',', ''))
            
            if 'Discount' in line:
                match = re.search(r'(\d+,?\d*\.?\d+)', line)
                if match:
                    totals["discount"] = float(match.group(1).replace(',', ''))
            
            if 'Taxable Amount' in line:
                match = re.search(r'(\d+,?\d*\.?\d+)', line)
                if match:
                    totals["taxable_amount"] = float(match.group(1).replace(',', ''))
            
            if 'GST Amount' in line:
                match = re.search(r'(\d+,?\d*\.?\d+)', line)
                if match:
                    totals["gst_amount"] = float(match.group(1).replace(',', ''))
            
            if 'Round Off' in line:
                match = re.search(r'(\d+\.?\d+)', line)
                if match:
                    totals["round_off"] = float(match.group(1))
            
            if 'Net Amount' in line:
                match = re.search(r'(\d+,?\d*\.?\d+)', line)
                if match:
                    totals["net_amount"] = float(match.group(1).replace(',', ''))
        
        return totals
    
    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        
        try:
            # Try DD/MM/YYYY format
            return datetime.strptime(date_str, "%d/%m/%Y")
        except:
            try:
                # Try MM/YYYY format for expiry
                return datetime.strptime(f"01/{date_str}", "%d/%m/%Y")
            except:
                return None
