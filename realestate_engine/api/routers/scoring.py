"""Router for scoring endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
import sys

sys.path.insert(0, '..')

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.scoring.scoring_engine import ScoringEngine
from realestate_engine.api.schemas.scoring import ScoringRequest, ScoringResponse

router = APIRouter()


def get_repository():
    """Dependency injection for database repository."""
    return DatabaseRepository()


def get_scoring_engine():
    """Dependency injection for scoring engine."""
    return ScoringEngine(DatabaseRepository())


@router.post("/", response_model=ScoringResponse)
async def score_property(
    request: ScoringRequest,
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
            if not all([request.preco_pedido, request.area_util_m2, request.quartos]):
                raise HTTPException(
                    status_code=400, 
                    detail="preco_pedido, area_util_m2, and quartos are required when not using listing_id"
                )
            
            # Create mock listing object
            from dataclasses import dataclass
            @dataclass
            class MockListing:
                preco_pedido: float
                area_util_m2: float
                quartos: int
                casas_banho: int = None
                freguesia: str = None
                concelho: str = None
                distrito: str = None
                lat: float = None
                lon: float = None
                estado: str = None
                ano_construcao: int = None
                cert_energetico: str = None
                tipologia: str = None
                preco_por_m2: float = None
                ine_preco_medio_m2: float = None
                ine_tendencia_mensal: float = None
                scrape_timestamp: str = None
                num_fotos: int = 0
                image_quality_score: float = None
                room_detection_confidence: float = None
                titulo: str = ""
                descricao: str = ""
                source_portal: str = "manual"
                dist_metro_m: float = None
                dist_escola_m: float = None
                dist_comercio_m: float = None
                cv_features: dict = None
                bert_sentiment_score: float = None
                bert_sentiment_label: str = None
                extracted_entities: dict = None
                description_summary: str = None
                description_quality_bert_score: float = None
                detected_rooms: int = None
                # Amenities
                tem_garagem: int = None
                tem_piscina: int = None
                tem_vista_mar: int = None
                tem_vista_rio: int = None
                tem_elevador: int = None
                tem_terraco: int = None
                tem_jardim: int = None
                tem_ac: int = None
                andar: int = None
                cozinha_separada: int = None
                tem_maquina_lavar: int = None
                tem_maquina_louca: int = None
                tem_frigorifico: int = None
                tem_fogao: int = None
                tem_forno: int = None
                tem_estores_anti_roubo: int = None
                tem_monitorizacao: int = None
                tem_videoporteiro: int = None
                tem_internet: int = None
                tem_tv_cabo: int = None
                tem_telefone: int = None
                acessibilidade_mobilidade: int = None
                tem_aquecimento: int = None
            
            # Calculate preco_por_m2
            preco_por_m2 = None
            if request.preco_pedido and request.area_util_m2:
                preco_por_m2 = request.preco_pedido / request.area_util_m2
            
            listing = MockListing(
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
            
            # Mock valuation
            from dataclasses import dataclass
            @dataclass
            class MockValuation:
                valor_justo: float
                discount: float = 0.0
                confianca: float = 0.5
                xgboost_explanation: dict = None
            
            # Estimate fair value (simple heuristic)
            estimated_fair = request.preco_pedido * 0.95  # Assume 5% discount on average
            valuation = MockValuation(
                valor_justo=estimated_fair,
                discount=0.05,
                confianca=0.5
            )
            
            result = engine.score(listing, valuation)
        
        return ScoringResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{listing_id}", response_model=ScoringResponse)
async def score_listing_by_id(
    listing_id: str,
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
        
        # Get listing from database if listing_id provided
        if listing_id:
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
            
            # Save score to database
            from realestate_engine.database.models import Score
            score = Score(
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
                has_critical_flags=result["has_critical_flags"],
                penalty_applied=result["penalty_applied"],
            )
            repo.create_scores_batch([score])
            
            return ScoringResponse(**result)
        
        else:
            # Create a CleanListing object from request
            from realestate_engine.database.models import CleanListing
            listing_dict = request.model_dump(exclude={'listing_id'})
            
            # Set required fields with defaults
            listing_dict.setdefault('is_sample', 0)
            listing_dict.setdefault('created_at', None)
            listing_dict.setdefault('updated_at', None)
            listing_dict.setdefault('source_portal', 'manual')
            listing_dict.setdefault('source_id', 'manual')
            listing_dict.setdefault('source_url', '')
            listing_dict.setdefault('titulo', '')
            listing_dict.setdefault('descricao', '')
            
            # Calculate preco_por_m2 if not provided
            if not listing_dict.get('preco_por_m2') and listing_dict.get('preco_pedido') and listing_dict.get('area_util_m2'):
                listing_dict['preco_por_m2'] = listing_dict['preco_pedido'] / listing_dict['area_util_m2']
            
            listing = CleanListing(**listing_dict)
            result = engine.score(listing)
            
            return ScoringResponse(**result)
        score = Score(
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
        )
        repo.create_scores_batch([score])
        
        return ScoringResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
