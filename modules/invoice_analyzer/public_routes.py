from fastapi import APIRouter, HTTPException
import os

router = APIRouter()

@router.get("/fields-guide")
def get_fields_guide():
    """Get invoice fields documentation - Public endpoint"""
    guide_path = os.path.join(os.path.dirname(__file__), "INVOICE_FIELDS_GUIDE.md")
    
    try:
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content, "format": "markdown"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fields guide not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading guide: {str(e)}")
