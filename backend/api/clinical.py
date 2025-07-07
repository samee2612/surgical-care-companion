"""
Clinical Data API Endpoints
Handles clinical assessments and medical data.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_clinical_data():
    """List clinical data - TODO: Implement"""
    return {"message": "Clinical data endpoints - Coming soon"}

@router.get("/assessments")
async def list_assessments():
    """List clinical assessments - TODO: Implement"""
    return {"message": "Clinical assessments - Coming soon"} 