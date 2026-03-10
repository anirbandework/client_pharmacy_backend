import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ExcelInvoiceExtractor:
    """Extract invoice data from Excel files"""
    
    @staticmethod
    def extract_from_excel(file_path: str) -> Dict[str, Any]:
        """Extract invoice data from Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)
            
            # Convert column names to lowercase for case-insensitive matching
            df.columns = df.columns.str.lower().str.strip()
            
            # Extract invoice header (first row or specific cells)
            invoice_data = {
                "invoice_number": ExcelInvoiceExtractor._get_value(df, "invoice_number", "invoice_no", "invoice no"),
                "invoice_date": ExcelInvoiceExtractor._get_date(df, "invoice_date", "invoice date", "date"),
                "due_date": ExcelInvoiceExtractor._get_date(df, "due_date", "due date"),
                "supplier_name": ExcelInvoiceExtractor._get_value(df, "supplier_name", "supplier", "vendor"),
                "supplier_address": ExcelInvoiceExtractor._get_value(df, "supplier_address", "address"),
                "supplier_gstin": ExcelInvoiceExtractor._get_value(df, "supplier_gstin", "gstin", "gst"),
                "supplier_dl_numbers": ExcelInvoiceExtractor._get_value(df, "supplier_dl_numbers", "dl_numbers", "dl"),
                "supplier_phone": ExcelInvoiceExtractor._get_value(df, "supplier_phone", "phone", "contact"),
                "items": [],
                "gross_amount": 0.0,
                "discount_amount": 0.0,
                "taxable_amount": 0.0,
                "total_gst": 0.0,
                "round_off": 0.0,
                "net_amount": 0.0
            }
            
            # Extract items (assuming items start from a certain row)
            items = ExcelInvoiceExtractor._extract_items(df)
            invoice_data["items"] = items
            
            # Calculate totals
            invoice_data["gross_amount"] = sum(item.get("taxable_amount", 0) for item in items)
            invoice_data["taxable_amount"] = invoice_data["gross_amount"]
            invoice_data["total_gst"] = sum(
                item.get("cgst_amount", 0) + item.get("sgst_amount", 0) + item.get("igst_amount", 0) 
                for item in items
            )
            invoice_data["net_amount"] = invoice_data["taxable_amount"] + invoice_data["total_gst"]
            
            logger.info(f"✅ Excel extraction successful - extracted {len(items)} items")
            return invoice_data
            
        except Exception as e:
            logger.error(f"❌ Excel extraction failed: {str(e)}")
            raise ValueError(f"Failed to parse Excel: {str(e)}")
    
    @staticmethod
    def _get_value(df: pd.DataFrame, *column_names) -> str:
        """Get value from DataFrame by trying multiple column names"""
        for col in column_names:
            if col in df.columns and not df[col].isna().all():
                val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                return str(val) if val is not None else None
        return None
    
    @staticmethod
    def _get_date(df: pd.DataFrame, *column_names) -> str:
        """Get date value and format as DD/MM/YYYY"""
        for col in column_names:
            if col in df.columns and not df[col].isna().all():
                val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if val:
                    try:
                        if isinstance(val, datetime):
                            return val.strftime("%d/%m/%Y")
                        elif isinstance(val, str):
                            # Try parsing common date formats
                            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]:
                                try:
                                    return datetime.strptime(val, fmt).strftime("%d/%m/%Y")
                                except:
                                    continue
                    except:
                        pass
        return None
    
    @staticmethod
    def _extract_items(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract items from DataFrame"""
        items = []
        
        # Required columns for items
        required_cols = ["product_name", "quantity", "unit_price"]
        
        # Check if we have item data
        has_items = any(col in df.columns for col in ["product_name", "product", "item_name", "item"])
        
        if not has_items:
            raise ValueError("Excel file must contain product/item information")
        
        # Map common column names
        col_mapping = {
            "product_name": ["product_name", "product", "item_name", "item", "medicine_name", "medicine", "brand name"],
            "composition": ["composition", "generic_name", "salt", "brand or generic"],
            "manufacturer": ["manufacturer", "mfg", "mfg_code"],
            "hsn_code": ["hsn_code", "hsn", "hsn_sac"],
            "batch_number": ["batch_number", "batch", "batch_no"],
            "quantity": ["quantity", "qty", "qnty"],
            "package": ["package", "pkg", "pack", "conversion"],
            "unit": ["unit", "uom", "unit_of_measure"],
            "manufacturing_date": ["manufacturing_date", "manufacturing date", "mfg_date", "mfg date", "mfg date"],
            "expiry_date": ["expiry_date", "expiry", "exp_date", "exp", "exp date"],
            "mrp": ["mrp", "max_retail_price"],
            "selling_price": ["selling_price", "selling price", "sale_price", "sales_price"],
            "profit_margin": ["profit_margin", "profit margin", "margin"],
            "discount_on_purchase": ["discount_on_purchase", "discount on purchase%", "purchase_discount", "discount_on_purchase%"],
            "discount_on_sales": ["discount_on_sales", "discount on sales%", "sales_discount", "discount_on_sales%"],
            "free_quantity": ["free_quantity", "free_qty", "free"],
            "unit_price": ["unit_price", "rate", "price", "unit_rate", "rate per unit"],
            "before_discount": ["before_discount", "before discount", "amount_before_discount", "gross_amount"],
            "discount_percent": ["discount_percent", "disc_%", "discount%"],
            "discount_amount": ["discount_amount", "discount", "disc_amt"],
            "taxable_amount": ["taxable_amount", "taxable", "amount", "amt", "taxable amount", "taxable rate"],
            "cgst_percent": ["cgst_percent", "cgst%", "cgst_rate", "cgst %"],
            "cgst_amount": ["cgst_amount", "cgst", "cgst_amt", "cgst amount"],
            "sgst_percent": ["sgst_percent", "sgst%", "sgst_rate", "sgst %"],
            "sgst_amount": ["sgst_amount", "sgst", "sgst_amt", "sgst amount"],
            "igst_percent": ["igst_percent", "igst%", "igst_rate"],
            "igst_amount": ["igst_amount", "igst", "igst_amt"],
            "taxed_amount": ["taxed_amount", "taxed amount", "total_with_tax", "total_amount", "total", "total_amt", "net_amount", "total payable"]
        }
        
        # Find actual column names
        actual_cols = {}
        for key, possible_names in col_mapping.items():
            for name in possible_names:
                if name in df.columns:
                    actual_cols[key] = name
                    break
        
        # Extract items row by row
        for idx, row in df.iterrows():
            # Skip rows without product name
            product_col = actual_cols.get("product_name")
            if not product_col or pd.isna(row[product_col]) or str(row[product_col]).strip() == "":
                continue
            
            # Extract item data
            item = {
                "composition": ExcelInvoiceExtractor._safe_get(row, actual_cols.get("composition")),
                "manufacturer": ExcelInvoiceExtractor._safe_get(row, actual_cols.get("manufacturer")),
                "hsn_code": ExcelInvoiceExtractor._safe_get(row, actual_cols.get("hsn_code")),
                "product_name": str(row[product_col]).strip(),
                "batch_number": ExcelInvoiceExtractor._safe_get(row, actual_cols.get("batch_number")),
                "quantity": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("quantity"), 1.0),
                "package": ExcelInvoiceExtractor._safe_get(row, actual_cols.get("package")),
                "unit": ExcelInvoiceExtractor._safe_get(row, actual_cols.get("unit")),
                "manufacturing_date": ExcelInvoiceExtractor._safe_date(row, actual_cols.get("manufacturing_date")),
                "expiry_date": ExcelInvoiceExtractor._safe_date(row, actual_cols.get("expiry_date")),
                "mrp": ExcelInvoiceExtractor._safe_get(row, actual_cols.get("mrp")),
                "selling_price": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("selling_price"), 0.0),
                "profit_margin": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("profit_margin"), 0.0),
                "discount_on_purchase": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("discount_on_purchase"), 0.0),
                "discount_on_sales": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("discount_on_sales"), 0.0),
                "free_quantity": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("free_quantity"), 0.0),
                "unit_price": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("unit_price"), 0.0),
                "before_discount": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("before_discount"), 0.0),
                "discount_percent": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("discount_percent"), 0.0),
                "discount_amount": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("discount_amount"), 0.0),
                "taxable_amount": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("taxable_amount"), 0.0),
                "cgst_percent": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("cgst_percent"), 0.0),
                "cgst_amount": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("cgst_amount"), 0.0),
                "sgst_percent": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("sgst_percent"), 0.0),
                "sgst_amount": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("sgst_amount"), 0.0),
                "igst_percent": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("igst_percent"), 0.0),
                "igst_amount": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("igst_amount"), 0.0),
                "total_amount": ExcelInvoiceExtractor._safe_float(row, actual_cols.get("taxed_amount"), 0.0)
            }
            
            # Auto-calculate if missing
            if item["before_discount"] == 0.0 and item["unit_price"] > 0:
                item["before_discount"] = item["quantity"] * item["unit_price"]
            
            if item["taxable_amount"] == 0.0:
                if item["before_discount"] > 0:
                    item["taxable_amount"] = item["before_discount"] - item["discount_amount"]
                else:
                    item["taxable_amount"] = item["quantity"] * item["unit_price"]
            
            if item["cgst_amount"] == 0.0 and item["cgst_percent"] > 0:
                item["cgst_amount"] = (item["taxable_amount"] * item["cgst_percent"]) / 100
            
            if item["sgst_amount"] == 0.0 and item["sgst_percent"] > 0:
                item["sgst_amount"] = (item["taxable_amount"] * item["sgst_percent"]) / 100
            
            if item["total_amount"] == 0.0:
                item["total_amount"] = item["taxable_amount"] + item["cgst_amount"] + item["sgst_amount"] + item["igst_amount"]
            
            items.append(item)
        
        if not items:
            raise ValueError("No valid items found in Excel file")
        
        return items
    
    @staticmethod
    def _safe_get(row, col_name) -> str:
        """Safely get string value from row"""
        if col_name and col_name in row.index and not pd.isna(row[col_name]):
            return str(row[col_name]).strip()
        return None
    
    @staticmethod
    def _safe_float(row, col_name, default=0.0) -> float:
        """Safely get float value from row"""
        if col_name and col_name in row.index and not pd.isna(row[col_name]):
            try:
                return float(row[col_name])
            except:
                pass
        return default
    
    @staticmethod
    def _safe_date(row, col_name) -> str:
        """Safely get date value from row"""
        if col_name and col_name in row.index and not pd.isna(row[col_name]):
            val = row[col_name]
            try:
                if isinstance(val, datetime):
                    # If day is 1st, format as MM/YYYY
                    if val.day == 1:
                        return val.strftime("%m/%Y")
                    return val.strftime("%d/%m/%Y")
                elif isinstance(val, str):
                    # Try parsing
                    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%Y"]:
                        try:
                            dt = datetime.strptime(val, fmt)
                            if fmt == "%m/%Y":
                                return val
                            return dt.strftime("%d/%m/%Y")
                        except:
                            continue
            except:
                pass
        return None
