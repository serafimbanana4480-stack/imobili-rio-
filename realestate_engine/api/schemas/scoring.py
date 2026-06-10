"""Pydantic schemas for scoring API."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class ScoringRequest(BaseModel):
    """Request schema for property scoring."""
    listing_id: Optional[str] = Field(None, description="Listing ID from database")
    preco_pedido: Optional[float] = Field(None, gt=0, description="Asking price")
    area_util_m2: Optional[float] = Field(None, gt=0, description="Usable area in m²")
    quartos: Optional[int] = Field(None, gt=0, description="Number of bedrooms")
    casas_banho: Optional[int] = Field(None, gt=0, description="Number of bathrooms")
    freguesia: Optional[str] = Field(None, description="Parish")
    concelho: Optional[str] = Field(None, description="Municipality")
    distrito: Optional[str] = Field(None, description="District")
    lat: Optional[float] = Field(None, description="Latitude")
    lon: Optional[float] = Field(None, description="Longitude")
    estado: Optional[str] = Field(None, description="Property condition")
    ano_construcao: Optional[int] = Field(None, description="Construction year")
    cert_energetico: Optional[str] = Field(None, description="Energy certificate")
    tipologia: Optional[str] = Field(None, description="Property type")
    ine_preco_medio_m2: Optional[float] = Field(None, description="INE average price per m²")
    ine_tendencia_mensal: Optional[float] = Field(None, description="INE monthly trend")
    scrape_timestamp: Optional[str] = Field(None, description="Scrape timestamp")
    num_fotos: Optional[int] = Field(None, description="Number of photos")
    source_portal: Optional[str] = Field(None, description="Source portal")
    titulo: Optional[str] = Field(None, description="Property title")
    descricao: Optional[str] = Field(None, description="Property description")


class ScoreCreate(BaseModel):
    """Schema for creating a score record."""
    listing_id: str
    score_total: float
    score_discount: Optional[float] = None
    score_location: Optional[float] = None
    score_condition: Optional[float] = None
    score_amenities: Optional[float] = None
    score_liquidity: Optional[float] = None
    score_freshness: Optional[float] = None
    classificacao: Optional[str] = None
    rationale: Optional[str] = None
    red_flags: Optional[List[str]] = None
    has_critical_flags: Optional[bool] = None
    penalty_applied: Optional[float] = None


class ScoringResponse(BaseModel):
    """Schema for scoring response."""
    score_total: float = Field(..., ge=0, le=10, description="Total score (0-10)")
    classificacao: str = Field(..., description="Classification (Imperdível, Excelente Oportunidade, etc.)")
    
    # Individual scores
    score_discount: Optional[float] = Field(None, ge=0, le=10, description="Discount score")
    score_location: Optional[float] = Field(None, ge=0, le=10, description="Location score")
    score_condition: Optional[float] = Field(None, ge=0, le=10, description="Condition score")
    score_amenities: Optional[float] = Field(None, ge=0, le=10, description="Amenities score")
    score_liquidity: Optional[float] = Field(None, ge=0, le=10, description="Liquidity score")
    score_freshness: Optional[float] = Field(None, ge=0, le=10, description="Freshness score")
    
    # Rationale and flags
    rationale: Optional[str] = Field(None, description="Score rationale")
    red_flags: Optional[List[str]] = Field(None, description="Red flags detected")
    has_critical_flags: Optional[bool] = Field(None, description="Has critical red flags")
    penalty_applied: Optional[float] = Field(None, description="Penalty applied to score")
