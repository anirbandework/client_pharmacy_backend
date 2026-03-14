# Stock Audit V2 — Complete System Documentation

**Module path:** `modules/stock_audit_v2/`
**Frontend path:** `client frontend/src/features/StockAudit/`
**DB prefix:** `stock_` (tables: `stock_racks`, `stock_sections_audit`, `stock_items_audit`, `purchases_audit`, `sales_audit`, `purchase_items_audit`, `sale_items_audit`, `stock_audit_records`, `stock_audit_sessions`, `stock_adjustments`, `excel_uploads`, `excel_upload_items`)

---

## 1. Purpose

Full inventory management system for a shop:
- Track physical stock with rack/section location
- Record purchases and sales
- Perform periodic physical audits (compare physical vs software count)
- Accept stock via Excel upload (two-level verified flow)
- Accept stock from AI-verified purchase invoices (`invoice_analyzer_v2`)
- Generate low-stock / expiry / movement reports
- AI analytics (comprehensive, charts, insights)

---

## 2. Data Model

### 2.1 Location Hierarchy

```
StockRack (stock_racks)
  └── StockSection (stock_sections_audit)   [many per rack]
        └── StockItem (stock_items_audit)   [many per section, or unassigned]
```

**StockRack fields:**
| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| shop_id | int FK → shops.id | data privacy scope |
| rack_number | str unique | e.g. "R1", "A" |
| location | str? | physical location description |
| description | text? | |

**StockSection fields:**
| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| shop_id | int FK → shops.id | |
| rack_id | int FK → stock_racks.id | |
| section_name | str | e.g. "Antibiotics" |
| section_code | str unique | e.g. "R1-A" |

### 2.2 StockItem — the core table

**Table:** `stock_items_audit`

| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| shop_id | int FK → shops.id | data privacy — always filter by this |
| section_id | int FK → stock_sections_audit.id, nullable | null = unassigned |
| product_name | str NOT NULL | indexed |
| batch_number | str NOT NULL | indexed; uniqueness is product_name+batch_number per shop |
| composition | str? | drug composition e.g. "Paracetamol 500mg" |
| manufacturer | str? | |
| hsn_code | str? | GST HSN code |
| package | str? | e.g. "10 tabs/strip" |
| unit | str? | e.g. "Strip", "Bottle" |
| manufacturing_date | date? | |
| expiry_date | date? | |
| mrp | str? | stored as string (may include ₹ symbol) |
| unit_price | float? | purchase cost per unit |
| selling_price | float? | |
| profit_margin | float? | percentage |
| quantity_software | int | authoritative software count |
| quantity_physical | int? | last recorded physical count |
| last_audit_date | datetime? | when physical count was last taken |
| audit_discrepancy | int | `quantity_software - quantity_physical`, 0 if never audited |
| source_invoice_id | int FK → purchase_invoices.id, nullable | set when created from invoice sync |
| created_at | datetime | |
| updated_at | datetime | |

**Lookup key:** `(shop_id, product_name, batch_number)` — used for deduplication during sync and Excel upload approval.

### 2.3 Purchase / Sale (manual entry)

These are manually entered transactions that also update `quantity_software`.

**Purchase** (`purchases_audit`): `shop_id, staff_id, purchase_date, supplier_name, invoice_number, total_amount`
**PurchaseItem** (`purchase_items_audit`): `purchase_id, stock_item_id, batch_number, quantity, unit_cost, total_cost`

**Sale** (`sales_audit`): `shop_id, staff_id, sale_date, customer_phone, bill_number, total_amount`
**SaleItem** (`sale_items_audit`): `sale_id, stock_item_id, batch_number, quantity, unit_price, total_price`

> When a Purchase is created, `stock_item.quantity_software += quantity`.
> When a Sale is created, `stock_item.quantity_software -= quantity`.

### 2.4 Audit Records & Sessions

**StockAuditRecord** (`stock_audit_records`): One record per item per audit event.
| Field | Type | Notes |
|---|---|---|
| stock_item_id | int FK | |
| shop_id / staff_id / staff_name | | who did it |
| audit_date | datetime | |
| software_quantity | int | snapshot at audit time |
| physical_quantity | int | what staff counted |
| discrepancy | int | software - physical |
| resolved | bool | admin can mark resolved |
| notes / reason_for_discrepancy | text | |

**StockAuditSession** (`stock_audit_sessions`): Groups an audit event.
Fields: `shop_id, staff_id, session_date, sections_audited, items_audited, discrepancies_found, status (in_progress/completed), started_at, completed_at, session_notes`

### 2.5 StockAdjustment

Manual quantity corrections outside of purchase/sale flow.
| Field | Type | Notes |
|---|---|---|
| stock_item_id | int FK | |
| adjustment_type | str | e.g. "add", "remove", "correction" |
| quantity_change | int | positive = add, negative = remove |
| reason | str NOT NULL | required |
| notes | text? | |
| adjustment_date | datetime | |

### 2.6 ExcelUpload / ExcelUploadItem

**ExcelUpload** (`excel_uploads`): One record per uploaded spreadsheet.
| Field | Type | Notes |
|---|---|---|
| shop_id | int FK | |
| filename | str | original filename |
| uploaded_by_staff_id/name | | uploader |
| uploaded_at | datetime | |
| staff_verified | bool | has staff verified? |
| staff_verified_by_id/name/at | | |
| admin_verified | bool | has admin approved? |
| admin_verified_by_id/name/at | | |
| status | str | see statuses below |
| total_items / success_count / error_count | int | parse stats |
| upload_notes / staff_notes / admin_notes / rejection_reason | text | |

**ExcelUpload statuses:**
```
pending_staff_verification  → staff reviews and verifies
pending_admin_verification  → admin reviews and approves
approved                    → items added to stock
rejected                    → rejected (staff or admin)
```

**ExcelUploadItem** (`excel_upload_items`): One row per item in the Excel file. Same fields as `StockItem` plus:
| Field | Type | Notes |
|---|---|---|
| upload_id | int FK → excel_uploads.id | |
| status | str | "pending" / "approved" / "rejected" |
| modified_by_staff / modified_by_admin | bool | edit tracking |
| stock_item_id | int FK → stock_items_audit.id, nullable | set after admin approval |

---

## 3. Workflow Diagrams

### 3.1 Excel Upload Verification Flow

```
Staff uploads Excel file
        │
        ▼
ExcelUpload created (status=pending_staff_verification)
ExcelUploadItems created (parsed from file)
        │
        ▼ Staff reviews items (edit/delete individual rows)
Staff calls POST /staff/uploads/{id}/staff-verify
        │
        ▼
status → pending_admin_verification
        │
        ▼ Admin reviews items (can still edit/delete rows)
Admin calls POST /admin/uploads/{id}/admin-verify
        │
        ├─ For each ExcelUploadItem:
        │     match by (shop_id, product_name, batch_number)
        │     ├── existing StockItem → quantity_software += item.quantity_software
        │     └── new → create StockItem from item fields
        │
        ▼
status → approved
ExcelUploadItem.stock_item_id set for each item
```

If rejected at any stage: `status → rejected`, `rejection_reason` stored.

### 3.2 Invoice Sync Flow (from invoice_analyzer_v2)

```
Admin approves a PurchaseInvoice in invoice_analyzer_v2
        │
        ▼
admin_routes.py: admin_verify_invoice()
        │
        ├── Mark invoice as verified (is_verified=True, is_admin_verified=True)
        │
        ├── Call InvoiceStockSyncService.sync_invoice_to_stock(db, invoice_id, shop_id)
        │       │
        │       ├── For each PurchaseInvoiceItem where product_name is not null:
        │       │     total_quantity = round(billed_qty + free_qty)
        │       │     Match by (shop_id, product_name, batch_number) in StockItem
        │       │     ├── existing → quantity_software += total_quantity
        │       │     └── new → create StockItem (source_invoice_id = invoice.id)
        │       │
        │       └── Returns stats dict (does NOT commit)
        │
        └── Single db.commit() covers both operations atomically
            (db.rollback() on any exception)
```

**Key file:** `modules/stock_audit_v2/sync_service.py` — `InvoiceStockSyncService.sync_invoice_to_stock()`

### 3.3 Physical Audit Flow

```
Staff requests random section: GET /staff/audit/random-section
        │
        ▼
System picks a random StockSection + its items
        │
        ▼
Staff optionally creates audit session: POST /staff/audit/sessions
        │
        ▼
For each item, staff enters physical count:
PUT /staff/items/{item_id}/audit?physical_quantity=N
        │
        ▼
StockAuditRecord created:
  software_quantity = current quantity_software snapshot
  physical_quantity = entered by staff
  discrepancy = software - physical
  stock_item.quantity_physical = N
  stock_item.last_audit_date = now
  stock_item.audit_discrepancy = discrepancy
```

---

## 4. API Endpoints

### 4.1 Staff Endpoints — prefix: `/api/stock-audit/staff`

**All staff endpoints filter by `staff.shop_id` (from JWT `sub`).**

#### Racks & Sections
| Method | Path | Description |
|---|---|---|
| POST | /racks | Create rack |
| GET | /racks | List racks (no pagination, small dataset) |
| PUT | /racks/{id} | Update rack |
| DELETE | /racks/{id} | Delete rack |
| POST | /sections | Create section |
| GET | /sections | List sections (optional `rack_id` filter) |
| PUT | /sections/{id} | Update section |
| DELETE | /sections/{id} | Delete section |

#### Stock Items
| Method | Path | Paginated | Notes |
|---|---|---|---|
| POST | /items | — | Create item manually |
| GET | /items | ✓ page/per_page=50 | Filters: section_id, search, expiry_before |
| GET | /items/unassigned/list | ✓ page/per_page=50 | Items with section_id=null |
| GET | /items/{id} | — | Single item |
| PUT | /items/{id} | — | Update item |
| DELETE | /items/{id} | — | Delete item |
| POST | /items/bulk-delete | — | Body: list of item IDs |
| PATCH | /items/{id}/assign-section | — | Query param: section_id |
| PUT | /items/{id}/audit | — | Query params: physical_quantity, notes |
| GET | /items/{id}/stock-calculation | — | Breakdown: purchases - sales + adjustments |

#### Excel Upload
| Method | Path | Paginated | Notes |
|---|---|---|---|
| POST | /items/upload-excel | — | multipart/form-data |
| GET | /uploads | ✓ page/per_page=20 | List uploads |
| GET | /uploads/{id}/items | — | Items in upload |
| PUT | /uploads/{id}/items/{item_id} | — | Edit item in upload |
| DELETE | /uploads/{id}/items/{item_id} | — | Delete item from upload |
| POST | /uploads/{id}/staff-verify | — | Body: {notes} |
| POST | /uploads/{id}/admin-verify | — | Body: {notes} (staff-accessible endpoint) |
| POST | /uploads/{id}/reject | — | Body: {reason} |
| DELETE | /uploads/{id} | — | Delete upload |

#### Purchases & Sales
| Method | Path | Paginated | Notes |
|---|---|---|---|
| POST | /purchases | — | |
| GET | /purchases | ✓ page/per_page=50 | |
| PUT | /purchases/{id} | — | |
| DELETE | /purchases/{id} | — | |
| POST | /sales | — | |
| GET | /sales | ✓ page/per_page=50 | |
| PUT | /sales/{id} | — | |
| DELETE | /sales/{id} | — | |

#### Audit
| Method | Path | Notes |
|---|---|---|
| GET | /audit/random-section | Returns RandomAuditSection schema |
| POST | /audit/sessions | Create audit session |
| GET | /audit/discrepancies | Items where discrepancy != 0 |
| GET | /audit/summary | Summary stats |

#### Stock Management
| Method | Path | Notes |
|---|---|---|
| POST | /calculate-stock | Recalculate quantity from purchase/sale history |
| POST | /adjustments | Create adjustment |
| GET | /adjustments | ✓ page/per_page=50 |

#### Reports & Analytics
| Method | Path | Notes |
|---|---|---|
| GET | /reports/low-stock | Items below threshold |
| GET | /reports/expiring | Items expiring within N days |
| GET | /reports/stock-movement | Movement report |
| GET | /ai-analytics/comprehensive | Gemini AI comprehensive analysis |
| GET | /ai-analytics/charts | Chart data |
| GET | /ai-analytics/insights | Key insights |

#### Exports
| Method | Path | Returns |
|---|---|---|
| GET | /export/stock-items | Excel blob |
| GET | /export/audit-records | Excel blob |
| GET | /export/adjustments | Excel blob |

### 4.2 Admin Endpoints — prefix: `/api/stock-audit/admin`

**All admin endpoints filter by `admin.organization_id` via JOIN on Shop table.**
Pattern: `.join(Shop).filter(Shop.organization_id == admin.organization_id)`

| Method | Path | Paginated | Notes |
|---|---|---|---|
| GET | /racks | — | All racks across org's shops |
| GET | /sections | — | Optional rack_id filter |
| GET | /uploads | ✓ page/per_page=20 | Optional status filter |
| GET | /uploads/{id}/items | — | |
| PUT | /uploads/{id}/items/{item_id} | — | Admin edit |
| DELETE | /uploads/{id}/items/{item_id} | — | Admin delete |
| POST | /uploads/{id}/admin-verify | — | Approves + syncs to stock |
| POST | /uploads/{id}/reject | — | |
| DELETE | /uploads/{id} | — | |
| GET | /analytics/dashboard | — | Org-wide dashboard stats |
| GET | /analytics/ai-insights | — | Gemini AI insights (timeout=120s) |
| GET | /export/stock-items | — | Excel blob |
| GET | /export/audit-records | — | Excel blob |
| GET | /export/adjustments | — | Excel blob |

---

## 5. Pagination

All list endpoints that can grow large use server-side pagination.

**Request params:** `page` (1-based, default 1), `per_page` (default varies)
**Response shape** (matches `PaginatedResponse[T]` in schemas.py):
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "per_page": 50,
  "pages": 3
}
```

**Default per_page values:**
- Stock items, purchases, sales, adjustments: **50**
- Excel uploads (staff + admin): **20**

**Endpoints that do NOT paginate** (small/bounded datasets):
- GET /racks — shops rarely have more than 20 racks
- GET /sections — filtered by rack_id, typically small
- GET /uploads/{id}/items — all items in one upload displayed together
- GET /audit/random-section, GET /audit/discrepancies, GET /audit/summary
- All POST/PUT/DELETE/PATCH endpoints

---

## 6. Frontend Architecture

### 6.1 Service Files
- `services/staff_stock_audit_apis.js` — all staff API calls, base `/api/stock-audit/staff`
- `services/admin_stock_audit_apis.js` — all admin API calls, base `/api/stock-audit/admin`

### 6.2 Staff Components (`components/staff_components/`)

| Component | What it does |
|---|---|
| `StockItems.jsx` | Main stock item list with tabs (All / Unassigned), search, pagination, add/edit/delete, bulk delete, section assignment |
| `StockAdjustments.jsx` | List adjustments + create new adjustment modal |
| `ExcelUploadVerification.jsx` | Upload Excel file + list uploads + view/edit/delete items + staff-verify flow |
| `RacksAndSections.jsx` | CRUD for racks and sections |
| `AuditSession.jsx` | Random section audit flow |
| `PurchasesAndSales.jsx` | Manual purchase/sale entry and listing |

### 6.3 Admin Components (`components/admin_components/`)

| Component | What it does |
|---|---|
| `ExcelVerification.jsx` | List all org's uploads with status filter, review items, approve/reject/delete |
| `AdminDashboard.jsx` | Dashboard stats and AI insights |

### 6.4 Shared Components (`components/shared/`)

| Component | What it does |
|---|---|
| `Pagination.jsx` | Reusable pagination UI. Props: `page, totalPages, total, perPage, onPageChange`. Renders Prev/numbered pages with ellipsis/Next + "Showing X–Y of Z". Returns null if totalPages <= 1. |

### 6.5 Pagination Pattern (used in all paginated components)

```jsx
const PER_PAGE = 50  // or 20 for uploads

const [items, setItems] = useState([])
const [page, setPage] = useState(1)
const [totalPages, setTotalPages] = useState(1)
const [total, setTotal] = useState(0)

const fetchData = async (p = 1) => {
  const res = await api.getItems({ page: p, per_page: PER_PAGE, ...filters })
  setItems(res.data.items)
  setTotal(res.data.total)
  setTotalPages(res.data.pages)
}

// Re-fetch when page changes
useEffect(() => { fetchData(page) }, [page])

// Reset to page 1 when filters change (use debounce if search field)
useEffect(() => { setPage(1); fetchData(1) }, [filter1, filter2])

// In render:
<Pagination page={page} totalPages={totalPages} total={total} perPage={PER_PAGE} onPageChange={setPage} />
```

**StockItems.jsx special case:** has two tabs (All / Unassigned) each with own pagination, and uses lightweight `per_page=1` calls to get badge counts for the inactive tab without fetching full data.

---

## 7. Data Privacy / Scoping Rules

### Staff queries
Every query must include `.filter(Model.shop_id == current_staff.shop_id)`
`current_staff` comes from `get_current_staff(token)` dependency (JWT sub = staff.id).

### Admin queries
Must JOIN Shop and filter by organization_id:
```python
.join(Shop).filter(Shop.organization_id == current_admin.organization_id)
```
This ensures admin only sees data for shops that belong to their organization.

### Who can do what
| Action | Staff | Admin |
|---|---|---|
| Create/edit/delete racks, sections, items | ✓ | ✗ (read-only via admin endpoints) |
| Upload Excel | ✓ | ✗ |
| Staff-verify upload | ✓ | ✗ |
| Admin-verify / reject upload | ✗ | ✓ |
| View dashboard / AI insights | Staff level AI | Admin org-wide |
| Export | ✓ (own shop) | ✓ (all shops in org) |

See `important_documents/auth_and_data_privacy.md` for full auth model details.

---

## 8. Link to invoice_analyzer_v2

### How invoices become stock

1. Staff uploads a purchase invoice PDF/image in `invoice_analyzer_v2` module
2. Gemini AI extracts items → staff reviews → staff verifies
3. Admin reviews → admin approves via `POST /api/invoice-analyzer/admin/{id}/verify`
4. The admin verify endpoint in `invoice_analyzer_v2/admin/admin_routes.py`:
   - Marks invoice `is_verified=True, is_admin_verified=True`
   - Calls `InvoiceStockSyncService.sync_invoice_to_stock(db, invoice_id, shop_id)`
   - Both steps in a single atomic `db.commit()` (rollback on failure)

### Sync logic (`sync_service.py`)
- Match key: `(shop_id, product_name, batch_number)`
- If match found → `quantity_software += round(billed_qty + free_qty)`
- If no match → create new `StockItem` with `source_invoice_id = invoice.id`
- Items with null `product_name` are skipped with a warning log
- Service does NOT commit — caller owns the transaction

### Reversal (`stock_reversal_service.py`)
If an admin-verified invoice is later rejected/reversed:
- Same match key `(shop_id, product_name, batch_number)`
- `quantity_software -= round(billed_qty + free_qty)`
- Null `product_name` items are skipped

---

## 9. Schemas (schemas.py key types)

```python
PaginatedResponse[T]    # Generic: {items, total, page, per_page, pages}
StoreRack               # id, rack_number, location, description
StoreSection            # id, rack_id, section_name, section_code
StockItem               # full item with section_name, rack_name, total_value computed
StockAuditRecord        # audit event with discrepancy
StockAuditSession       # session grouping audit events
Purchase / PurchaseItem
Sale / SaleItem
StockAdjustment
RandomAuditSection      # {section, items_to_audit, total_items, message}
StockDiscrepancy        # {item, software_qty, physical_qty, difference, ...}
StockSummary            # {total_items, total_sections, items_with_discrepancies, ...}
```

---

## 10. Common Gotchas

1. **Unique constraint on `section_code`** — must be globally unique across all shops (not per-shop). Plan codes carefully.

2. **`quantity_software` is the source of truth.** Never directly SET it except during sync/upload approval. Always use `+=` or `-=` in transactions.

3. **`source_invoice_id`** — only set when item was created by invoice sync. Items created manually or via Excel upload have this as null.

4. **Excel upload admin-verify in staff routes** — there is a `/staff/uploads/{id}/admin-verify` endpoint in staff_routes.py (line 683) in addition to the proper admin route. This is likely legacy — the primary admin-verify path is through the admin router.

5. **ORDER BY in paginated queries** — items list is ordered by `product_name` server-side. Do not sort client-side as it would only sort the current page.

6. **`audit_discrepancy` on StockItem** — this is a denormalized cached value updated each time `PUT /items/{id}/audit` is called. The authoritative history is in `stock_audit_records`.

7. **StockSection `shop_id`** — sections are scoped to a shop even though they belong to a rack. Always filter sections by `shop_id` from the authenticated user.
