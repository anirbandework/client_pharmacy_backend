# Invoice Fields Guide

This guide explains every field in a purchase invoice. Use it as a reference when verifying or editing an invoice.

---

## Header Fields

| Field | Description | Example |
|---|---|---|
| **Invoice Number** | Unique number printed on the supplier's invoice. Auto-generated if not found. | `GMPL/TR/25-26/SW000217` |
| **Invoice Date** | Date the supplier issued the invoice. Format: DD/MM/YYYY. | `27/09/2025` |
| **Due Date** | Payment due date (if mentioned on invoice). | `27/10/2025` |
| **Supplier Name** | Name of the pharmaceutical distributor or company. | `Anjali Drug Agency` |
| **Supplier Address** | Registered address of the supplier. | `Melarmath, Agartala` |
| **Supplier GSTIN** | 15-character GST Identification Number of the supplier. | `16DKZPR0183R1ZX` |
| **Supplier DL Numbers** | Drug License numbers of the supplier (may be two — WLF20 & WLF21). | `WLF20B2025TR000022` |
| **Supplier Phone** | Contact number of the supplier. | `9862494794` |

---

## Item-Level Fields

| Field | Description | Example |
|---|---|---|
| **Product Name** | Name of the medicine or product. | `Paracetamol 500mg Tab` |
| **Composition** | Generic/salt name of the medicine. | `Paracetamol` |
| **Manufacturer** | Company that manufactured the product. | `Cipla Ltd` |
| **HSN Code** | 8-digit HSN/SAC code for GST classification. | `30049099` |
| **Batch Number** | Manufacturing batch number printed on the strip/bottle. | `B240612` |
| **Quantity** | Number of units (strips, bottles, etc.) purchased. | `10` |
| **Package** | Pack size (e.g. 10×10 means 10 strips of 10 tablets). | `10X10` |
| **Unit** | Unit of measurement (Strip, Bottle, Tube, etc.). | `Strip` |
| **Manufacturing Date** | Date of manufacture. Format: MM/YYYY or DD/MM/YYYY. | `06/2024` |
| **Expiry Date** | Expiry date printed on the pack. Format: MM/YYYY or DD/MM/YYYY. | `06/2026` |
| **MRP** | Maximum Retail Price printed on the pack (in ₹). | `₹85.50` |
| **Selling Price** | Price at which you plan to sell to customers. Must be ≤ MRP. | `₹80.00` |
| **Profit Margin %** | `(Selling Price − Purchase Rate) / Selling Price × 100` | `15.5%` |

---

## Pricing Fields

| Field | Description | Example |
|---|---|---|
| **Unit Price / Rate** | Purchase rate per unit charged by the supplier (before discount). | `₹72.00` |
| **Before Discount** | Gross amount = Quantity × Unit Price. | `₹720.00` |
| **Discount %** | Trade discount percentage offered by supplier. | `5%` |
| **Discount Amount** | Rupee value of the discount applied. | `₹36.00` |
| **Taxable Amount** | Amount after discount, before GST. | `₹684.00` |
| **Free Quantity** | Number of free units given by supplier (bonus stock). | `1` |
| **Discount on Purchase %** | Additional purchase discount percentage. | `2%` |
| **Discount on Sales %** | Discount percentage you offer to customers. | `5%` |

---

## GST Fields

| Field | Description | Example |
|---|---|---|
| **CGST %** | Central GST rate (applies to intra-state purchases). | `6%` |
| **CGST Amount** | CGST in rupees = Taxable Amount × CGST %. | `₹41.04` |
| **SGST %** | State GST rate (applies to intra-state purchases). | `6%` |
| **SGST Amount** | SGST in rupees = Taxable Amount × SGST %. | `₹41.04` |
| **IGST %** | Integrated GST rate (applies to inter-state purchases). | `12%` |
| **IGST Amount** | IGST in rupees = Taxable Amount × IGST %. | `₹82.08` |
| **Total Amount** | Final item total = Taxable Amount + CGST + SGST + IGST. | `₹766.08` |

> **Note:** For intra-state purchases CGST + SGST apply. For inter-state purchases only IGST applies.

---

## Invoice Totals

| Field | Description |
|---|---|
| **Gross Amount** | Sum of all item amounts before any discounts. |
| **Total Discount** | Total discount given across all items. |
| **Taxable Amount** | Total amount after discount, before GST. |
| **Total GST** | Sum of all CGST + SGST + IGST across all items. |
| **Round Off** | Small rounding adjustment (typically ±₹1). |
| **Net Amount** | Final payable amount = Taxable Amount + Total GST ± Round Off. |

---

## Verification Status

| Status | Meaning |
|---|---|
| **Staff Verification Required** | Invoice uploaded but not yet reviewed by staff. |
| **Awaiting Admin Approval** | Staff has verified — waiting for admin to approve. |
| **Admin Verified** | Fully approved. Invoice is locked. |
| **Rejected – Reverify** | Admin found an issue. Staff must correct and re-submit. |
