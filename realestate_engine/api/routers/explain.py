"""Explainability endpoints for Real Estate Engine API."""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from loguru import logger

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.valuation.xgboost_model import XGBoostModel
from realestate_engine.api.middleware.auth import optional_auth
from realestate_engine.api.middleware.rate_limit import rate_limit, RATE_LIMITS

router = APIRouter()


class ExplainabilityResponse(BaseModel):
    """Schema for explainability response."""
    listing_id: str
    predicted_price: float
    top_features: List[Dict[str, Any]]
    location_effect: float
    explanation_ready: bool


def get_repository():
    return DatabaseRepository()


def get_xgboost_model():
    model = XGBoostModel()
    try:
        model.load_model()
    except Exception as e:
        logger.warning(f"Could not load XGBoost model: {e}")
    return model


@router.get("/{listing_id}", response_model=ExplainabilityResponse)
@rate_limit(RATE_LIMITS["valuation"])
async def explain_listing(
    request: Request,
    listing_id: str,
    current_user: dict = Depends(optional_auth),
    repo: DatabaseRepository = Depends(get_repository),
    model: XGBoostModel = Depends(get_xgboost_model),
):
    """Return SHAP explainability for a listing valuation."""
    try:
        listing = repo.get_clean_listing_by_id(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        if not model.is_trained:
            raise HTTPException(status_code=503, detail="Valuation model not trained yet")

        listing_dict = {
            "preco_pedido": listing.preco_pedido,
            "area_util_m2": listing.area_util_m2,
            "quartos": listing.quartos,
            "casas_banho": listing.casas_banho,
            "ano_construcao": listing.ano_construcao,
            "freguesia": listing.freguesia,
            "concelho": listing.concelho,
            "distrito": listing.distrito,
            "lat": listing.lat,
            "lon": listing.lon,
            "estado": listing.estado,
            "cert_energetico": listing.cert_energetico,
            "tipologia": listing.tipologia,
            "preco_por_m2": listing.preco_por_m2,
            "dist_metro_m": getattr(listing, "dist_metro_m", None),
            "dist_escola_m": getattr(listing, "dist_escola_m", None),
        }

        prediction_explanations = model.predict_with_explanation(listing_dict)
        if prediction_explanations is None or not isinstance(prediction_explanations, (list, tuple)) or len(prediction_explanations) != 2:
            raise HTTPException(status_code=503, detail="Could not generate explanation")
        
        prediction, explanations = prediction_explanations

        if prediction is None:
            raise HTTPException(status_code=503, detail="Could not generate explanation")

        if not isinstance(explanations, dict):
            raise HTTPException(status_code=503, detail="Invalid explanation format")

        top_features = sorted(
            ((k, v) for k, v in explanations.items() if k != "freguesia_effect"),
            key=lambda x: abs(x[1]),
            reverse=True,
        )[:5]

        return ExplainabilityResponse(
            listing_id=listing_id,
            predicted_price=round(prediction, 2),
            top_features=[{"feature": k, "impact": round(v, 4)} for k, v in top_features],
            location_effect=round(explanations.get("freguesia_effect", 0), 4),
            explanation_ready=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explainability error for {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
