# Purchase Invoice Fields - Complete Guide

This guide explains all fields captured from purchase invoices (PDF/Excel) in the system. Each field is automatically extracted and can be edited during verification.

---

## Duplicate Detection

The system prevents duplicate invoice uploads using two checks:

**Check 1: Invoice Number Match**
- Checks if the same invoice number already exists for your shop
- Most reliable method to prevent duplicates
- Error shown: "Duplicate invoice detected! Invoice number 'XXX' already exists (Invoice ID: 123)."

**Check 2: Similar Invoice Detection**
- Checks if an invoice with same supplier name, same date, and same amount already exists
- Catches cases where invoice number might be different but it's the same invoice
- Error shown: "Possible duplicate invoice detected! A similar invoice from 'Supplier Name' with same date (31/07/2025) and amount (₹45,273.00) already exists (Invoice: XXX)."

**What happens when duplicate is detected:**
- Upload is rejected immediately
- Uploaded file is deleted from server
- Detailed error message shows which existing invoice matches
- You can review the existing invoice before deciding to upload again

---

## Compulsory Fields

These fields MUST be present for successful invoice processing:

**Invoice Header:**
- Invoice Number
- Invoice Date
- Supplier Name

**Item Level (Per Product):**
- Product Name
- Batch Number
- Quantity
- Expiry Date
- Unit Price
- Taxable Amount
- CGST Percent & Amount
- SGST Percent & Amount
- Total Amount

---

## Excel Template Columns

When using Excel import, use these exact column names:

| Column Name | Description | Required | Example |
|-------------|-------------|----------|----------|
| **Composition** | Generic/salt name | No | `Paracetamol 500mg` |
| **Product Name** | Brand name | Yes | `CROCIN 500` |
| **Manufacturer** | Manufacturer code | No | `GSPL` |
| **HSN Code** | 8-digit HSN code | No | `30049099` |
| **Batch Number** | Batch/lot number | Yes | `ABC123` |
| **Quantity** | Units purchased | Yes | `10` |
| **Free Quantity** | Free units | No | `2` |
| **Package** | Packaging format | No | `10 X 10` |
| **Unit** | Unit type | No | `Strip` |
| **Manufacturing Date** | Mfg date | No | `01/2025` |
| **Expiry Date** | Expiry date | Yes | `12/2026` |
| **MRP** | Maximum retail price | No | `50.00/STRIP` |
| **Unit Price** | Purchase price | Yes | `35.50` |
| **Selling Price** | Your selling price | No | `45.00` |
| **Profit Margin** | Profit percentage | No | `15` |
| **Discount on Purchase** | Supplier discount | No | `5` |
| **Discount on Sales** | Customer discount | No | `2` |
| **Before Discount** | Pre-discount amount | No | `400.00` |
| **Discount Percent** | Discount % | No | `5` |
| **Discount Amount** | Discount value | No | `20.00` |
| **Taxable Amount** | Base for tax | Yes | `355.00` |
| **CGST Percent** | CGST rate | Yes | `9` |
| **CGST Amount** | CGST value | Yes | `31.95` |
| **SGST Percent** | SGST rate | Yes | `9` |
| **SGST Amount** | SGST value | Yes | `31.95` |
| **IGST Percent** | IGST rate | No | `0` |
| **IGST Amount** | IGST value | No | `0` |
| **Total Amount** | Final total | Yes | `418.90` |

---

## Invoice Header Fields

### Invoice Information
| Field | Description | Example | Required |
|-------|-------------|---------|----------|
| **Invoice Number** | Unique invoice identifier from supplier | `GMPL/TR/25-26/SW000106` | ✅ Yes |
| **Invoice Date** | Date when invoice was issued | `31/07/2025` | ✅ Yes |
| **Due Date** | Payment due date | `31/08/2025` | ❌ No |

### Supplier Information
| Field | Description | Example | Required |
|-------|-------------|---------|----------|
| **Supplier Name** | Name of the supplier/vendor | `Anjali Drug Agency` | ✅ Yes |
| **Supplier Address** | Complete supplier address | `Melarmath Kalibari Road, Agartala` | ❌ No |
| **Supplier GSTIN** | 15-digit GST identification number | `16DKZPR0183R1ZX` | ❌ No |
| **Supplier DL Numbers** | Drug license numbers (comma-separated) | `WLF20B2025TR000022, WLF21B2025TR000021` | ❌ No |
| **Supplier Phone** | 10-digit contact number | `9862494794` | ❌ No |

### Financial Summary
| Field | Description | Example | Auto-Calculated |
|-------|-------------|---------|-----------------|
| **Gross Amount** | Total before taxes | `₹40,565.59` | ✅ Yes |
| **Discount Amount** | Total discount applied | `₹0.00` | ✅ Yes |
| **Taxable Amount** | Amount on which tax is calculated | `₹40,565.59` | ✅ Yes |
| **CGST Amount** | Central GST total | `₹2,353.51` | ✅ Yes |
| **SGST Amount** | State GST total | `₹2,353.51` | ✅ Yes |
| **IGST Amount** | Integrated GST total (inter-state) | `₹0.00` | ✅ Yes |
| **Total GST** | Sum of all GST | `₹4,707.02` | ✅ Yes |
| **Round Off** | Rounding adjustment | `₹0.42` | ❌ Manual |
| **Net Amount** | Final payable amount | `₹45,273.00` | ✅ Yes |

---

## Item-Level Fields (Per Product)

### Product Identification
| Field | Description | Example | Source | Required |
|-------|-------------|---------|--------|----------|
| **Composition** | Generic/salt name of medicine | `Paracetamol 500mg` | Manual/Excel | ❌ No |
| **Product Name** | Brand name of product | `ADMELIV-400 TAB` | PDF/Excel | ✅ Yes |
| **Manufacturer** | Manufacturer code (usually 4 letters) | `CLEV` | PDF/Excel | ❌ No |
| **HSN Code** | 8-digit Harmonized System code for taxation | `21069099` | PDF/Excel | ❌ No |
| **Batch Number** | Unique batch/lot number | `FC-004` | PDF/Excel | ✅ Yes |

### Quantity & Packaging
| Field | Description | Example | Source | Required |
|-------|-------------|---------|--------|----------|
| **Quantity** | Number of units purchased | `10` | PDF/Excel | ✅ Yes |
| **Free Quantity** | Bonus units given free (e.g., Buy 10 Get 2 Free) | `2` | PDF/Excel | ❌ No |
| **Package** | Packaging format | `10 X 10` (10 strips of 10 tablets) | PDF/Excel | ❌ No |
| **Unit** | Unit of measurement | `Strip`, `Box`, `Bottle` | Manual/Excel | ❌ No |

**Free Quantity Explained:**
- Suppliers often give extra units for free as promotional offers
- Example: "Buy 10 Get 2 Free" means Quantity=10, Free Quantity=2
- Total received = Quantity + Free Quantity = 12 units
- You only pay for the purchased quantity (10), not the free ones
- This increases your profit margin significantly

### Dates
| Field | Description | Format | Example | Required |
|-------|-------------|--------|---------|----------|
| **Manufacturing Date** | When product was manufactured | `MM/YYYY` | `01/2025` | ❌ No |
| **Expiry Date** | Product expiration date | `MM/YYYY` | `09/2026` | ✅ Yes |

### Pricing
| Field | Description | Example | Auto-Calculated | Required |
|-------|-------------|---------|-----------------|----------|
| **MRP** | Maximum Retail Price (printed on product) | `960.00/STRIP` | ❌ No | ❌ No |
| **Unit Price** | Purchase price per unit | `₹427.22` | ❌ No | ✅ Yes |
| **Selling Price** | Your selling price to customers | `₹850.00` | ❌ Manual | ❌ No |
| **Profit Margin** | Profit percentage | `15%` | ✅ Yes (if selling price set) | ❌ No |

**Profit Margin Calculation:**
```
Profit Margin % = ((Selling Price - Unit Price) / Unit Price) × 100
Example: ((850 - 427.22) / 427.22) × 100 = 98.9%
```

### Discounts
| Field | Description | Example | Source | Required |
|-------|-------------|---------|--------|----------|
| **Discount on Purchase** | Discount given by supplier | `₹50.00` or `5%` | PDF/Excel | ❌ No |
| **Discount on Sales** | Discount you offer to customers | `₹20.00` or `2%` | Manual | ❌ No |
| **Before Discount** | Amount before discount applied | `₹5,000.00` | PDF/Excel | ❌ No |
| **Discount Percent** | Discount percentage | `5%` | PDF/Excel | ❌ No |
| **Discount Amount** | Absolute discount value | `₹250.00` | ✅ Yes | ❌ No |

### Tax Details (GST)
| Field | Description | Example | Auto-Calculated | Required |
|-------|-------------|---------|-----------------|----------|
| **Taxable Amount** | Base amount for tax calculation | `₹4,272.20` | ✅ Yes | ✅ Yes |
| **CGST Percent** | Central GST rate | `9%` | PDF/Excel | ✅ Yes |
| **CGST Amount** | Central GST value | `₹384.50` | ✅ Yes | ✅ Yes |
| **SGST Percent** | State GST rate | `9%` | PDF/Excel | ✅ Yes |
| **SGST Amount** | State GST value | `₹384.50` | ✅ Yes | ✅ Yes |
| **IGST Percent** | Integrated GST rate (inter-state) | `18%` | PDF/Excel | ❌ No |
| **IGST Amount** | Integrated GST value | `₹0.00` | ✅ Yes | ❌ No |
| **Total Amount** | Final item total (Taxable + GST) | `₹5,041.20` | ✅ Yes | ✅ Yes |

**GST Explained:**
- **CGST + SGST**: Used for intra-state purchases (within same state)
  - Example: 18% GST = 9% CGST + 9% SGST
- **IGST**: Used for inter-state purchases (different states)
  - Example: 18% IGST (no CGST/SGST)
- Common GST rates: 0%, 5%, 12%, 18%, 28%
- Medicines typically have: 0%, 5%, 12%, or 18% GST

**Tax Calculation Example:**
```
Taxable Amount: ₹4,272.20
CGST @ 9%: ₹384.50
SGST @ 9%: ₹384.50
Total: ₹5,041.20
```

---

## Field Usage by Module

### Stock Management
Uses: Product Name, Batch Number, Quantity, Free Quantity, Expiry Date, Unit Price

### Billing System
Uses: Product Name, Batch Number, MRP, Selling Price, GST rates, Stock availability

### Profit Analysis
Uses: Unit Price, Selling Price, Profit Margin, Quantity, Discounts

### Expiry Tracking
Uses: Product Name, Batch Number, Expiry Date, Quantity

---

## Data Sources

### PDF Extraction (AI-Powered OCR)
- Automatically extracts all visible fields from PDF invoices
- Uses pattern recognition for Indian pharmaceutical invoices
- Handles multiple invoice formats
- Extracts: Product Name, Manufacturer, HSN, Batch, Quantity, Package, Expiry, MRP, Prices, GST

### Excel Import
- Reads structured data from Excel templates
- Supports custom column mapping
- More accurate than PDF for structured data
- Can include additional fields like Composition, Unit, Manufacturing Date

### Manual Entry/Editing
- All fields can be manually edited during verification
- Add missing information not captured by OCR
- Correct any extraction errors
- Add custom fields specific to your business

---

## Verification Checklist

Before marking an invoice as verified, check:

1. ✅ **Invoice Number** is correct and unique
2. ✅ **Supplier Name** matches your records
3. ✅ **All Product Names** are correctly extracted (not null)
4. ✅ **Batch Numbers** are present for all items
5. ✅ **Quantities** match the physical stock received
6. ✅ **Expiry Dates** are in correct format (MM/YYYY)
7. ✅ **Prices** (Unit Price, MRP) are accurate
8. ✅ **GST Rates** are correct for each product
9. ✅ **Totals** match the invoice footer
10. ✅ **Free Quantities** are recorded if applicable

---

## Custom Fields

You can add shop-specific custom fields for:
- Internal product codes
- Shelf locations
- Supplier-specific notes
- Special handling instructions
- Warranty information
- Any other business-specific data

Custom fields are stored separately and don't affect standard calculations.

---

## Tips for Better Data Capture

### For PDF Invoices:
- Use high-quality scans (300 DPI or higher)
- Ensure text is clear and not blurry
- Avoid handwritten invoices (use typed/printed)
- Keep invoice format consistent from suppliers

### For Excel Imports:
- Use the provided template format
- Fill all mandatory columns
- Use consistent date formats (DD/MM/YYYY or MM/YYYY)
- Don't leave empty rows between items

### For Manual Verification:
- Always verify product names (most critical)
- Double-check batch numbers and expiry dates
- Confirm quantities match physical stock
- Validate GST calculations
- Add free quantities if mentioned on invoice

---

## Support

If you encounter issues with field extraction or need help understanding any field, contact your system administrator or refer to the main documentation.

**Last Updated:** March 2026
**Version:** 1.0
