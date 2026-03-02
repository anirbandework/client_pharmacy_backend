from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from datetime import datetime
from .dependencies import get_current_user_with_geofence as get_current_user

router = APIRouter()

@router.get("/download-template")
def download_excel_template(current_user: tuple = Depends(get_current_user)):
    """Download Excel template for invoice upload (requires authentication)"""
    staff, shop_id = current_user  # Ensures only authenticated staff can download
    
    # Create comprehensive sample data with 2 rows
    template_data = {
        "Invoice_Number": ["INV-001", ""],
        "Invoice_Date": ["15/01/2024", ""],
        "Supplier_Name": ["ABC Pharmaceuticals", ""],
        "Supplier_GSTIN": ["29ABCDE1234F1Z5", ""],
        "Supplier_Phone": ["9876543210", ""],
        "Composition": ["Paracetamol 500mg", "Amoxicillin 250mg"],
        "Brand Name": ["Dolo 650", "Amoxil"],
        "Manufacturer": ["CIPLA", "SUN"],
        "HSN_Code": ["30049099", "30042064"],
        "Package": ["10 X 10", "10 X 6"],
        "Unit": ["Box", "Strip"],
        "Quantity": [10, 5],
        "Manufacturing date": ["01/2024", "02/2024"],
        "Expiry_Date": ["12/2025", "06/2026"],
        "MRP": ["5.00/STRIP", "120.00/STRIP"],
        "selling price": [4.0, 100.0],
        "Profit margin": [20, 25],
        "Discount on purchase%": [10, 15],
        "Discount on sales%": [5, 8],
        "Taxable amount": [2000, 1500],
        "CGST_Percent": [2.5, 6.0],
        "CGST Amount": [50, 90],
        "SGST_Percent": [2.5, 6.0],
        "SGST Amount": [50, 90],
        "Taxed amount": [2100, 1680],
    }
    
    # Create DataFrame
    df = pd.DataFrame(template_data)
    
    # Create Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Invoice', index=False)
        
        # Add instructions sheet
        instructions = pd.DataFrame({
            "Column Name": [
                "Invoice_Number", "Invoice_Date", "Supplier_Name", "Supplier_GSTIN",
                "Composition", "Brand Name", "Manufacturer", "HSN_Code",
                "Package", "Unit", "Quantity", "Manufacturing date", "Expiry_Date",
                "MRP", "selling price", "Profit margin", "Discount on purchase%",
                "Taxable amount", "CGST_Percent", "CGST Amount", "SGST_Percent", "SGST Amount"
            ],
            "Required": [
                "Yes", "Yes", "Yes", "No",
                "No", "Yes", "No", "No",
                "No", "No", "Yes", "No", "No",
                "No", "No", "No", "No",
                "No", "No", "No", "No", "No"
            ],
            "Description": [
                "Unique invoice number (fill only in first row)",
                "Date in DD/MM/YYYY format (fill only in first row)",
                "Supplier/Vendor name (fill only in first row)",
                "15-digit GSTIN (fill only in first row)",
                "Generic/Salt name (e.g., Paracetamol 500mg)",
                "Brand/Product name (required for each item)",
                "Manufacturer code (e.g., CIPLA, SUN)",
                "8-digit HSN code",
                "Package info (e.g., 10 X 10)",
                "Unit type (Box, Strip, Bottle, etc.)",
                "Quantity purchased (required)",
                "Manufacturing date (MM/YYYY or DD/MM/YYYY)",
                "Expiry date (MM/YYYY or DD/MM/YYYY)",
                "MRP with unit (e.g., 5.00/STRIP)",
                "Selling price per unit",
                "Profit margin percentage",
                "Purchase discount percentage",
                "Taxable amount (auto-calculated if empty)",
                "CGST percentage (auto-calculated if empty)",
                "CGST amount (auto-calculated if empty)",
                "SGST percentage (auto-calculated if empty)",
                "SGST amount (auto-calculated if empty)"
            ]
        })
        instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        # Add field reference sheet
        field_reference = pd.DataFrame({
            "Category": [
                "Invoice Header", "Invoice Header", "Invoice Header", "Invoice Header",
                "Product Info", "Product Info", "Product Info", "Product Info",
                "Packaging", "Packaging", "Quantity", "Dates", "Dates",
                "Pricing", "Pricing", "Pricing", "Discounts",
                "Tax", "Tax", "Tax", "Tax", "Tax"
            ],
            "Field": [
                "Invoice_Number", "Invoice_Date", "Supplier_Name", "Supplier_GSTIN",
                "Composition", "Brand Name", "Manufacturer", "HSN_Code",
                "Package", "Unit", "Quantity", "Manufacturing date", "Expiry_Date",
                "MRP", "selling price", "Profit margin", "Discount on purchase%",
                "Taxable amount", "CGST_Percent", "CGST Amount", "SGST_Percent", "SGST Amount"
            ],
            "Example": [
                "INV-001", "15/01/2024", "ABC Pharmaceuticals", "29ABCDE1234F1Z5",
                "Paracetamol 500mg", "Dolo 650", "CIPLA", "30049099",
                "10 X 10", "Box", "10", "01/2024", "12/2025",
                "5.00/STRIP", "4.0", "20", "10",
                "2000", "2.5", "50", "2.5", "50"
            ]
        })
        field_reference.to_excel(writer, sheet_name='Field Reference', index=False)
    
        # Format the sheets
        workbook = writer.book
        
        # Format Invoice sheet
        invoice_sheet = workbook['Invoice']
        for cell in invoice_sheet[1]:
            cell.font = cell.font.copy(bold=True)
            cell.fill = cell.fill.copy(fgColor="D3D3D3")
        
        # Format Instructions sheet
        instructions_sheet = workbook['Instructions']
        for cell in instructions_sheet[1]:
            cell.font = cell.font.copy(bold=True)
            cell.fill = cell.fill.copy(fgColor="90EE90")
        
        # Format Field Reference sheet
        reference_sheet = workbook['Field Reference']
        for cell in reference_sheet[1]:
            cell.font = cell.font.copy(bold=True)
            cell.fill = cell.fill.copy(fgColor="87CEEB")
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=purchase_invoice_template.xlsx"}
    )
