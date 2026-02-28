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
    
    # Create sample data with 2 rows
    template_data = {
        "Invoice_Number": ["INV-001", ""],
        "Invoice_Date": ["15/01/2024", ""],
        "Supplier_Name": ["ABC Pharmaceuticals", ""],
        "Supplier_GSTIN": ["29ABCDE1234F1Z5", ""],
        "Supplier_Phone": ["9876543210", ""],
        "Product_Name": ["Paracetamol 500mg", "Amoxicillin 250mg"],
        "Manufacturer": ["CIPLA", "SUN"],
        "HSN_Code": ["30049099", "30042064"],
        "Batch_Number": ["BATCH001", "BATCH002"],
        "Quantity": [100, 50],
        "Package": ["10 X 10", "10 X 6"],
        "Expiry_Date": ["12/2025", "06/2026"],
        "MRP": ["5.00/STRIP", "120.00/STRIP"],
        "Unit_Price": [3.50, 85.00],
        "CGST_Percent": [6.0, 6.0],
        "SGST_Percent": [6.0, 6.0],
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
                "Invoice_Number", "Invoice_Date", "Supplier_Name", "Product_Name", 
                "Quantity", "Unit_Price", "CGST_Percent", "SGST_Percent"
            ],
            "Required": ["Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "No", "No"],
            "Description": [
                "Unique invoice number (fill only in first row)",
                "Date in DD/MM/YYYY format (fill only in first row)",
                "Supplier/Vendor name (fill only in first row)",
                "Product/Medicine name (required for each item)",
                "Quantity purchased",
                "Rate per unit",
                "CGST percentage (e.g., 6.0)",
                "SGST percentage (e.g., 6.0)"
            ]
        })
        instructions.to_excel(writer, sheet_name='Instructions', index=False)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=invoice_template.xlsx"}
    )
