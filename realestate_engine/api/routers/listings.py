"""Router for listings endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from typing import Optional, List
from loguru import logger
import sys
from slowapi import Limiter

sys.path.insert(0, '..')

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.api.schemas.listings import (
    ListingResponse,
    ListingListResponse,
    ListingFilter
)
from realestate_engine.api.middleware.rate_limit import rate_limit, RATE_LIMITS

router = APIRouter()
limiter = Limiter(key_func=lambda: "client")


def get_repository():
    """Dependency injection for database repository."""
    return DatabaseRepository()


@router.get("/", response_model=ListingListResponse)
@limiter.limit(RATE_LIMITS["listings"])
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
        # Build filters dict
        filters = {}
        if concelho:
            filters["concelho"] = concelho
        if distrito:
            filters["distrito"] = distrito
        if source_portal:
            filters["source_portal"] = source_portal
        
        # Get listings from database
        all_listings = repo.get_clean_listings(filters=filters if filters else None, limit=1000)
        
        # Apply numeric filters in Python (since DB doesn't support range queries in this simple implementation)
        filtered_listings = []
        for listing in all_listings:
            # Price filter
            if preco_min and listing.preco_pedido < preco_min:
                continue
            if preco_max and listing.preco_pedido > preco_max:
                continue
            
            # Area filter
            if area_min and listing.area_util_m2 < area_min:
                continue
            if area_max and listing.area_util_m2 > area_max:
                continue
            
            # Bedrooms filter
            if quartos_min and listing.quartos < quartos_min:
                continue
            if quartos_max and listing.quartos > quartos_max:
                continue
            
            filtered_listings.append(listing)
        
        # Paginate
        total = len(filtered_listings)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_listings = filtered_listings[start_idx:end_idx]
        
        # Convert to response schema
        listings = []
        for listing in paginated_listings:
            listings.append(ListingResponse(
                id=listing.id,
                source_portal=listing.source_portal,
                source_id=listing.source_id,
                source_url=listing.source_url,
                titulo=listing.titulo,
                descricao=listing.descricao[:500] if listing.descricao else "",
                preco_pedido=listing.preco_pedido,
                area_util_m2=listing.area_util_m2,
                quartos=listing.quartos,
                casas_banho=listing.casas_banho,
                concelho=listing.concelho,
                distrito=listing.distrito,
                freguesia=listing.freguesia,
                lat=listing.lat,
                lon=listing.lon,
                scrape_timestamp=listing.scrape_timestamp
            ))
        
        return ListingListResponse(
            listings=listings,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
        
    except Exception as e:
        logger.error(f"Error fetching listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
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
        
        return ListingResponse(
            id=listing.id,
            titulo=listing.titulo,
            descricao=listing.descricao,
            preco_pedido=listing.preco_pedido,
            area_util_m2=listing.area_util_m2,
            quartos=listing.quartos,
            casas_banho=listing.casas_banho,
            freguesia=listing.freguesia,
            concelho=listing.concelho,
            distrito=listing.distrito,
            estado=listing.estado,
            ano_construcao=listing.ano_construcao,
            cert_energetico=listing.cert_energetico,
            tipologia=listing.tipologia,
            preco_por_m2=listing.preco_por_m2,
            lat=listing.lat,
            lon=listing.lon,
            source_portal=listing.source_portal,
            source_url=listing.source_url,
            scrape_timestamp=listing.scrape_timestamp,
            created_at=listing.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
