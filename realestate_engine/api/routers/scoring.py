"""Router for scoring endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Request
from loguru import logger
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.api.schemas.scoring import ScoringRequest, ScoringResponse
from realestate_engine.api.middleware.auth import optional_auth
from realestate_engine.api.middleware.rate_limit import rate_limit, RATE_LIMITS

router = APIRouter()


def get_repository():
    """Dependency injection for database repository."""
    return DatabaseRepository()


def get_scoring_engine():
    """Dependency injection for scoring engine."""
    return ScoringEngine(DatabaseRepository())


@dataclass
class PropertyData:
    """Lightweight property data container for manual scoring."""
    preco_pedido: float
    area_util_m2: float
    quartos: int
    casas_banho: Optional[int] = None
    freguesia: Optional[str] = None
    concelho: Optional[str] = None
    distrito: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    estado: Optional[str] = None
    ano_construcao: Optional[int] = None
    cert_energetico: Optional[str] = None
    tipologia: Optional[str] = None
    preco_por_m2: Optional[float] = None
    ine_preco_medio_m2: Optional[float] = None
    ine_tendencia_mensal: Optional[float] = None
    num_fotos: int = 0
    source_portal: str = "manual"
    titulo: str = ""
    descricao: str = ""
    tem_garagem: int = 0
    tem_piscina: int = 0
    tem_vista_mar: int = 0
    tem_vista_rio: int = 0
    tem_elevador: int = 0
    tem_terraco: int = 0
    tem_jardim: int = 0
    tem_ac: int = 0
    andar: Optional[int] = None
    cozinha_separada: int = 0
    tem_aquecimento: int = 0
    dist_metro_m: Optional[float] = None
    dist_escola_m: Optional[float] = None
    dist_comercio_m: Optional[float] = None
    cv_features: Optional[Dict[str, Any]] = None
    bert_sentiment_score: Optional[float] = None
    bert_sentiment_label: Optional[str] = None
    extracted_entities: Optional[Dict[str, Any]] = None
    description_summary: Optional[str] = None
    description_quality_bert_score: Optional[float] = None
    detected_rooms: Optional[int] = None
    tem_maquina_lavar: int = 0
    tem_maquina_louca: int = 0
    tem_frigorifico: int = 0
    tem_fogao: int = 0
    tem_forno: int = 0
    tem_estores_anti_roubo: int = 0
    tem_monitorizacao: int = 0
    tem_videoporteiro: int = 0
    tem_internet: int = 0
    tem_tv_cabo: int = 0
    tem_telefone: int = 0
    acessibilidade_mobilidade: int = 0
    scrape_timestamp: Optional[str] = None
    image_quality_score: Optional[float] = None
    room_detection_confidence: Optional[float] = None


@dataclass
class ValuationData:
    """Lightweight valuation data container for manual scoring."""
    valor_justo: float
    discount: float = 0.0
    confianca: float = 0.5
    xgboost_explanation: Optional[Dict[str, Any]] = None


@router.post("/", response_model=ScoringResponse)
@rate_limit(RATE_LIMITS["scoring"])
async def score_property(
    request: Request,
    request_body: ScoringRequest,
    current_user: dict = Depends(optional_auth),
    repo: DatabaseRepository = Depends(get_repository),
    engine: ScoringEngine = Depends(get_scoring_engine)
):
    """
    Score a property using multi-factor scoring algorithm.
    
    Args:
        request: Property data for scoring (either listing_id or property data)
    
    Returns:
        Score result with total score and classification
    """
    try:
        logger.info(f"Scoring property: {request.listing_id or 'manual data'}")
        
        # If listing_id provided, get from database
        if request.listing_id:
            listing = repo.get_clean_listing_by_id(request.listing_id)
            if not listing:
                raise HTTPException(status_code=404, detail="Listing not found")
            
            # Get valuation (required for discount score)
            valuation = repo.get_valuation_by_listing(request.listing_id)
            if not valuation:
                raise HTTPException(status_code=400, detail="Listing must be valuated first")
            
            # Score using database objects
            result = engine.score(listing, valuation)
            
        else:
            # Manual scoring - need all required fields
            if request.preco_pedido is None or request.area_util_m2 is None or request.quartos is None:
                raise HTTPException(
                    status_code=400, 
                    detail="preco_pedido, area_util_m2, and quartos are required when not using listing_id"
                )
            
            # Calculate preco_por_m2
            preco_por_m2 = None
            if request.preco_pedido and request.area_util_m2:
                preco_por_m2 = request.preco_pedido / request.area_util_m2
            
            listing = PropertyData(
                preco_pedido=request.preco_pedido,
                area_util_m2=request.area_util_m2,
                quartos=request.quartos,
                casas_banho=request.casas_banho,
                freguesia=request.freguesia,
                concelho=request.concelho,
                distrito=request.distrito,
                lat=request.lat,
                lon=request.lon,
                estado=request.estado,
                ano_construcao=request.ano_construcao,
                cert_energetico=request.cert_energetico,
                tipologia=request.tipologia,
                ine_preco_medio_m2=request.ine_preco_medio_m2,
                ine_tendencia_mensal=request.ine_tendencia_mensal,
                preco_por_m2=preco_por_m2,
            )
            
            # For manual scoring, require a manual valuation or fail gracefully
            raise HTTPException(
                status_code=400,
                detail="Manual scoring requires a prior valuation. Please valuate the property first or provide a listing_id."
            )
        
        return ScoringResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{listing_id}", response_model=ScoringResponse)
@rate_limit(RATE_LIMITS["scoring"])
async def score_listing_by_id(
    request: Request,
    listing_id: str,
    current_user: dict = Depends(optional_auth),
    repo: DatabaseRepository = Depends(get_repository),
    engine: ScoringEngine = Depends(get_scoring_engine)
):
    """
    Score a listing from the database by ID.
    
    Args:
        listing_id: Listing UUID
    
    Returns:
        Score result
    """
    try:
        logger.info(f"Scoring listing by ID: {listing_id}")
        
        # Get listing from database
        listing = repo.get_clean_listing_by_id(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Check if score already exists
        existing_score = repo.get_score_by_listing(listing_id)
        if existing_score:
            logger.info(f"Returning existing score for listing {listing_id}")
            return ScoringResponse(
                score_total=existing_score.score_total,
                classificacao=existing_score.classificacao,
                score_discount=existing_score.score_discount,
                score_location=existing_score.score_location,
                score_condition=existing_score.score_condition,
                score_amenities=existing_score.score_amenities,
                score_liquidity=existing_score.score_liquidity,
                score_freshness=existing_score.score_freshness,
                rationale=existing_score.rationale,
                red_flags=existing_score.red_flags,
                has_critical_flags=None,
                penalty_applied=None
            )
        
        # Get valuation (required)
        valuation = repo.get_valuation_by_listing(listing_id)
        if not valuation:
            raise HTTPException(status_code=400, detail="Listing must be valuated first")
        
        # Score
        result = engine.score(listing, valuation)
        
        # Save score to database using validated schema
        from realestate_engine.database.models import Score
        from realestate_engine.api.schemas.scoring import ScoreCreate
        
        score_data = ScoreCreate(
            listing_id=listing.id,
            score_total=result["score_total"],
            score_discount=result["score_discount"],
            score_location=result["score_location"],
            score_condition=result["score_condition"],
            score_liquidity=result["score_liquidity"],
            score_freshness=result["score_freshness"],
            classificacao=result["classificacao"],
            rationale=result["rationale"],
            red_flags=result["red_flags"],
            has_critical_flags=result.get("has_critical_flags"),
            penalty_applied=result.get("penalty_applied"),
        )
        score = Score(**score_data.model_dump())
        repo.create_scores_batch([score])
        
        return ScoringResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
