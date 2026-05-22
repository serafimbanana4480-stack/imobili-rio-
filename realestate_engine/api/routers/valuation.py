"""Router for valuation endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
import sys

sys.path.insert(0, '..')

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.api.schemas.valuation import (
    ValuationRequest,
    ValuationResponse,
    AdvancedValuationResponse
)

router = APIRouter()


def get_repository():
    """Dependency injection for database repository."""
    return DatabaseRepository()


def get_valuation_engine():
    """Dependency injection for valuation engine."""
    return ValuationEngine()


@router.post("/", response_model=ValuationResponse)
async def valuate_property(
    request: ValuationRequest,
    use_advanced: bool = False,
    repo: DatabaseRepository = Depends(get_repository),
    engine: ValuationEngine = Depends(get_valuation_engine)
):
    """
    Valuate a property using ML ensemble.
    
    Args:
        request: Property data for valuation
        use_advanced: If True, use 8-model ensemble (slower but more accurate)
    
    Returns:
        Valuation result with fair value and confidence interval
    """
    try:
        logger.info(f"Valuating property: {request.concelho}, {request.freguesia}, €{request.preco_pedido}")
        
        # Convert request to dict
        listing_dict = request.dict()
        
        # Get pool of comparable listings
        pool = None
        if request.concelho:
            filters = {"concelho": request.concelho}
            listings = repo.get_clean_listings(filters=filters, limit=1000)
            pool = [
                {
                    "preco_pedido": l.preco_pedido,
                    "area_util_m2": l.area_util_m2,
                    "quartos": l.quartos,
                    "casas_banho": l.casas_banho,
                    "freguesia": l.freguesia,
                    "concelho": l.concelho,
                    "distrito": l.distrito,
                    "lat": l.lat,
                    "lon": l.lon,
                    "estado": l.estado,
                    "ano_construcao": l.ano_construcao,
                    "cert_energetico": l.cert_energetico,
                    "tipologia": l.tipologia,
                    "preco_por_m2": l.preco_por_m2,
                }
                for l in listings
            ]
        
        # Perform valuation
        if use_advanced:
            result = engine.valuate_advanced(listing_dict, pool)
            if not result:
                raise HTTPException(status_code=400, detail="Valuation failed - insufficient data")
            return AdvancedValuationResponse(**result)
        else:
            result = engine.valuate(listing_dict, pool)
            if not result:
                raise HTTPException(status_code=400, detail="Valuation failed - insufficient data")
            return ValuationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error valuating property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{listing_id}", response_model=ValuationResponse)
async def valuate_listing_by_id(
    listing_id: str,
    use_advanced: bool = False,
    repo: DatabaseRepository = Depends(get_repository),
    engine: ValuationEngine = Depends(get_valuation_engine)
):
    """
    Valuate a listing from the database by ID.
    
    Args:
        listing_id: Listing UUID
        use_advanced: If True, use 8-model ensemble
    
    Returns:
        Valuation result
    """
    try:
        logger.info(f"Valuating listing by ID: {listing_id}")
        
        # Get listing from database
        listing = repo.get_clean_listing_by_id(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Check if valuation already exists
        existing_valuation = repo.get_valuation_by_listing(listing_id)
        if existing_valuation:
            logger.info(f"Returning existing valuation for listing {listing_id}")
            return ValuationResponse(
                valor_justo=existing_valuation.valor_justo,
                ci_lower=existing_valuation.ci_lower,
                ci_upper=existing_valuation.ci_upper,
                confianca=existing_valuation.confianca,
                discount=existing_valuation.discount,
                valuation_quality=None,
                value_risk=None,
                hedonic_value=existing_valuation.hedonic_value,
                comps_value=existing_valuation.comps_value,
                ine_value=existing_valuation.ine_value,
                xgboost_value=existing_valuation.xgboost_value,
                xgboost_explanation=existing_valuation.xgboost_explanation,
                ensemble_weights=None,
            )
        
        # Convert to dict
        listing_dict = {
            "preco_pedido": listing.preco_pedido,
            "area_util_m2": listing.area_util_m2,
            "quartos": listing.quartos,
            "casas_banho": listing.casas_banho,
            "freguesia": listing.freguesia,
            "concelho": listing.concelho,
            "distrito": listing.distrito,
            "lat": listing.lat,
            "lon": listing.lon,
            "estado": listing.estado,
            "ano_construcao": listing.ano_construcao,
            "cert_energetico": listing.cert_energetico,
            "tipologia": listing.tipologia,
            "preco_por_m2": listing.preco_por_m2,
        }
        
        # Get pool
        filters = {"concelho": listing.concelho}
        listings = repo.get_clean_listings(filters=filters, limit=1000)
        pool = [
            {
                "preco_pedido": l.preco_pedido,
                "area_util_m2": l.area_util_m2,
                "quartos": l.quartos,
                "casas_banho": l.casas_banho,
                "freguesia": l.freguesia,
                "concelho": l.concelho,
                "distrito": l.distrito,
                "lat": l.lat,
                "lon": l.lon,
            }
            for l in listings
        ]
        
        # Perform valuation
        if use_advanced:
            result = engine.valuate_advanced(listing_dict, pool)
        else:
            result = engine.valuate(listing_dict, pool)
        
        if not result:
            raise HTTPException(status_code=400, detail="Valuation failed - insufficient data")
        
        # Save valuation to database
        from realestate_engine.database.models import Valuation
        valuation = Valuation(
            listing_id=listing.id,
            valor_justo=result["valor_justo"],
            hedonic_value=result.get("hedonic_value"),
            comps_value=result.get("comps_value"),
            ine_value=result.get("ine_value"),
            xgboost_value=result.get("xgboost_value"),
            xgboost_explanation=result.get("xgboost_explanation"),
            ci_lower=result["ci_lower"],
            ci_upper=result["ci_upper"],
            discount=result.get("discount"),
            confianca=result["confianca"],
        )
        repo.create_valuations_batch([valuation])
        
        return ValuationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error valuating listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
