"""Router for listings endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from typing import Optional, List
from loguru import logger

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.api.schemas.listings import (
    ListingResponse,
    ListingListResponse,
    ListingFilter
)
from realestate_engine.api.middleware.rate_limit import rate_limit, RATE_LIMITS

router = APIRouter()


def get_repository():
    """Dependency injection for database repository."""
    return DatabaseRepository()


@router.get("/", response_model=ListingListResponse)
@rate_limit(RATE_LIMITS["listings"])
async def get_listings(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Page size"),
    concelho: Optional[str] = Query(None, description="Filter by municipality"),
    distrito: Optional[str] = Query(None, description="Filter by district"),
    preco_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    preco_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    area_min: Optional[float] = Query(None, ge=0, description="Minimum area"),
    area_max: Optional[float] = Query(None, ge=0, description="Maximum area"),
    quartos_min: Optional[int] = Query(None, ge=0, description="Minimum bedrooms"),
    quartos_max: Optional[int] = Query(None, ge=0, description="Maximum bedrooms"),
    source_portal: Optional[str] = Query(None, description="Filter by source portal"),
    repo: DatabaseRepository = Depends(get_repository)
):
    """Get paginated listings with optional filters."""
    try:
        # Build exact-match filters dict
        filters = {}
        if concelho:
            filters["concelho"] = concelho
        if distrito:
            filters["distrito"] = distrito
        if source_portal:
            filters["source_portal"] = source_portal
        
        # SQL-level pagination and filtering
        offset = (page - 1) * page_size
        listings = repo.get_clean_listings(
            filters=filters if filters else None,
            limit=page_size,
            offset=offset,
            preco_min=preco_min,
            preco_max=preco_max,
            area_min=area_min,
            area_max=area_max,
            quartos_min=quartos_min,
            quartos_max=quartos_max,
        )
        
        # Convert to response schema using model_validate
        listings_response = [ListingResponse.model_validate(listing) for listing in listings]
        
        # Get total count for pagination metadata
        total = repo.get_total_clean_listings_count()
        
        return ListingListResponse(
            listings=listings_response,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
        
    except Exception as e:
        logger.error(f"Error fetching listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{listing_id}", response_model=ListingResponse)
@rate_limit(RATE_LIMITS["listings"])
async def get_listing(
    request: Request,
    listing_id: str,
    repo: DatabaseRepository = Depends(get_repository)
):
    """
    Get a specific listing by ID.
    
    Args:
        listing_id: Listing UUID
    
    Returns:
        Listing details
    """
    try:
        logger.info(f"Fetching listing: {listing_id}")
        
        listing = repo.get_clean_listing_by_id(listing_id)
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        return ListingResponse.model_validate(listing)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
