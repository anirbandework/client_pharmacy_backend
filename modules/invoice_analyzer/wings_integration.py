from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import logging
import json

from .models import PurchaseInvoice, PurchaseInvoiceItem, ItemSale
from .schemas import PurchaseInvoiceCreate, PurchaseInvoiceItemCreate, ItemSaleCreate
from .service import PurchaseInvoiceService

logger = logging.getLogger(__name__)

class WINGSIntegrationService:
    """Service for integrating with WINGS POS system"""
    
    @staticmethod
    def import_purchase_invoice_from_wings(db: Session, wings_data: Dict[str, Any], shop_id: Optional[int] = None) -> PurchaseInvoice:
        """Import purchase invoice from WINGS with item-wise details"""
        
        try:
            # Parse WINGS purchase data format
            invoice_data = PurchaseInvoiceCreate(
                invoice_number=wings_data["invoice_number"],
                supplier_name=wings_data["supplier_name"],
                invoice_date=datetime.strptime(wings_data["invoice_date"], "%Y-%m-%d").date(),
                received_date=datetime.strptime(wings_data["received_date"], "%Y-%m-%d").date(),
                items=[
                    PurchaseInvoiceItemCreate(
                        item_code=item["item_code"],
                        item_name=item["item_name"],
                        batch_number=item.get("batch_number"),
                        purchased_quantity=float(item["quantity"]),
                        unit_cost=float(item["unit_cost"]),
                        selling_price=float(item["selling_price"]),
                        expiry_date=datetime.strptime(item["expiry_date"], "%Y-%m-%d").date() if item.get("expiry_date") else None
                    )
                    for item in wings_data["items"]
                ]
            )
            
            # Create invoice using existing service
            invoice = PurchaseInvoiceService.create_invoice(db, invoice_data, shop_id)
            
            logger.info(f"Successfully imported WINGS purchase invoice {invoice.invoice_number}")
            return invoice
            
        except Exception as e:
            logger.error(f"Error importing WINGS purchase invoice: {str(e)}")
            raise ValueError(f"Failed to import WINGS purchase data: {str(e)}")
    
    @staticmethod
    def import_sales_from_wings(db: Session, wings_sales_data: List[Dict[str, Any]]) -> List[ItemSale]:
        """Import sales data from WINGS with item-wise details"""
        
        imported_sales = []
        
        for sale_data in wings_sales_data:
            try:
                # Find the corresponding item by code and batch
                item = db.query(PurchaseInvoiceItem).filter(
                    PurchaseInvoiceItem.item_code == sale_data["item_code"],
                    PurchaseInvoiceItem.batch_number == sale_data.get("batch_number")
                ).order_by(PurchaseInvoiceItem.id.desc()).first()
                
                if not item:
                    # Try without batch number
                    item = db.query(PurchaseInvoiceItem).filter(
                        PurchaseInvoiceItem.item_code == sale_data["item_code"]
                    ).order_by(PurchaseInvoiceItem.id.desc()).first()
                
                if not item:
                    logger.warning(f"Item not found for WINGS sale: {sale_data['item_code']}")
                    continue
                
                # Create sale record
                sale_create = ItemSaleCreate(
                    item_id=item.id,
                    quantity_sold=float(sale_data["quantity_sold"]),
                    sale_price=float(sale_data["sale_price"]),
                    customer_type=sale_data.get("customer_type", "walk-in")
                )
                
                # Record sale
                sale = PurchaseInvoiceService.record_sale(db, sale_create)
                imported_sales.append(sale)
                
            except Exception as e:
                logger.error(f"Error importing WINGS sale {sale_data}: {str(e)}")
                continue
        
        logger.info(f"Successfully imported {len(imported_sales)} sales from WINGS")
        return imported_sales
    
    @staticmethod
    def sync_with_wings_live(db: Session, wings_api_endpoint: str, shop_code: str) -> Dict[str, Any]:
        """Sync live data from WINGS POS system"""
        
        sync_result = {
            "status": "success",
            "shop_code": shop_code,
            "sync_timestamp": datetime.utcnow(),
            "purchases_imported": 0,
            "sales_imported": 0,
            "errors": []
        }
        
        try:
            # Mock WINGS API call - replace with actual API integration
            logger.info(f"Live sync with WINGS completed for shop {shop_code}")
            
        except Exception as e:
            sync_result["status"] = "error"
            sync_result["errors"].append(str(e))
            logger.error(f"WINGS sync error: {str(e)}")
        
        return sync_result
    
    @staticmethod
    def validate_wings_purchase_data(wings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate WINGS purchase data format"""
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Required fields validation
        required_fields = ["invoice_number", "supplier_name", "invoice_date", "received_date", "items"]
        
        for field in required_fields:
            if field not in wings_data:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing required field: {field}")
        
        # Items validation
        if "items" in wings_data:
            for i, item in enumerate(wings_data["items"]):
                required_item_fields = ["item_code", "item_name", "quantity", "unit_cost", "selling_price"]
                
                for field in required_item_fields:
                    if field not in item:
                        validation_result["valid"] = False
                        validation_result["errors"].append(f"Item {i+1}: Missing required field: {field}")
                
                # Validate numeric fields
                numeric_fields = ["quantity", "unit_cost", "selling_price"]
                for field in numeric_fields:
                    if field in item:
                        try:
                            float(item[field])
                        except (ValueError, TypeError):
                            validation_result["valid"] = False
                            validation_result["errors"].append(f"Item {i+1}: Invalid numeric value for {field}")
        
        return validation_result
    
    @staticmethod
    def validate_wings_sales_data(wings_sales_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate WINGS sales data format"""
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        for i, sale in enumerate(wings_sales_data):
            required_fields = ["item_code", "quantity_sold", "sale_price"]
            
            for field in required_fields:
                if field not in sale:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Sale {i+1}: Missing required field: {field}")
            
            # Validate numeric fields
            numeric_fields = ["quantity_sold", "sale_price"]
            for field in numeric_fields:
                if field in sale:
                    try:
                        float(sale[field])
                    except (ValueError, TypeError):
                        validation_result["valid"] = False
                        validation_result["errors"].append(f"Sale {i+1}: Invalid numeric value for {field}")
        
        return validation_result