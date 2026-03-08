# Auto-Populate Selling Price & Profit Margin

## Feature Overview

When staff edits the composition field in the invoice edit section, the system automatically fetches and populates the selling price and profit margin based on historical data from verified invoices.

## API Endpoint

**GET** `/api/purchase-invoices/pricing/by-composition`

### Query Parameters
- `composition` (required): The composition/generic name to lookup (e.g., "Paracetamol 500mg")

### Authentication
- Requires staff or admin authentication
- Staff can only see data from their shop
- Admin can see data across all shops in their organization

### Response Format

```json
{
  "selling_price": 45.50,
  "profit_margin": 15.25,
  "found": true
}
```

If no data found:
```json
{
  "selling_price": null,
  "profit_margin": null,
  "found": false
}
```

## Frontend Implementation

### Example Usage (React/Vue/Angular)

```javascript
// When composition field changes
const handleCompositionChange = async (composition) => {
  if (!composition || composition.trim() === '') return;
  
  try {
    const response = await fetch(
      `/api/purchase-invoices/pricing/by-composition?composition=${encodeURIComponent(composition)}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const data = await response.json();
    
    if (data.found) {
      // Auto-populate the fields
      setSellingPrice(data.selling_price);
      setProfitMargin(data.profit_margin);
      
      // Optional: Show a notification
      showNotification('Pricing data auto-populated from previous invoices');
    }
  } catch (error) {
    console.error('Failed to fetch pricing data:', error);
  }
};
```

### React Hook Example

```javascript
import { useState, useEffect } from 'react';

const usePricingByComposition = (composition) => {
  const [pricing, setPricing] = useState({ selling_price: null, profit_margin: null });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!composition) return;

    const fetchPricing = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `/api/purchase-invoices/pricing/by-composition?composition=${encodeURIComponent(composition)}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            }
          }
        );
        const data = await response.json();
        if (data.found) {
          setPricing({
            selling_price: data.selling_price,
            profit_margin: data.profit_margin
          });
        }
      } catch (error) {
        console.error('Error fetching pricing:', error);
      } finally {
        setLoading(false);
      }
    };

    // Debounce the API call
    const timer = setTimeout(fetchPricing, 500);
    return () => clearTimeout(timer);
  }, [composition]);

  return { ...pricing, loading };
};

// Usage in component
const InvoiceItemEdit = () => {
  const [composition, setComposition] = useState('');
  const [sellingPrice, setSellingPrice] = useState('');
  const [profitMargin, setProfitMargin] = useState('');
  
  const { selling_price, profit_margin, loading } = usePricingByComposition(composition);

  useEffect(() => {
    if (selling_price !== null) {
      setSellingPrice(selling_price);
    }
    if (profit_margin !== null) {
      setProfitMargin(profit_margin);
    }
  }, [selling_price, profit_margin]);

  return (
    <div>
      <input
        value={composition}
        onChange={(e) => setComposition(e.target.value)}
        placeholder="Composition"
      />
      {loading && <span>Loading pricing...</span>}
      <input
        value={sellingPrice}
        onChange={(e) => setSellingPrice(e.target.value)}
        placeholder="Selling Price"
      />
      <input
        value={profitMargin}
        onChange={(e) => setProfitMargin(e.target.value)}
        placeholder="Profit Margin %"
      />
    </div>
  );
};
```

## How It Works

1. **Data Source**: Fetches from admin-verified invoices only (ensures data quality)
2. **Matching**: Case-insensitive exact match on composition field
3. **Selection**: Returns the most recent invoice item with both selling_price > 0 and profit_margin > 0
4. **Scope**: 
   - Staff: Only their shop's data
   - Admin: All shops in their organization

## Benefits

- **Time Saving**: No need to manually enter pricing for repeat items
- **Consistency**: Maintains consistent pricing across invoices
- **Accuracy**: Uses verified historical data
- **User Experience**: Seamless auto-population without page refresh

## Notes

- The endpoint only returns data if both selling_price and profit_margin are present in historical data
- Staff can still manually override the auto-populated values
- The lookup is based on exact composition match (case-insensitive)
- Only admin-verified invoices are used as data source
