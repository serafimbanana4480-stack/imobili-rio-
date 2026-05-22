"""Pydantic schemas for listings API."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ListingBase(BaseModel):
    """Base listing schema."""
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    preco_pedido: float
    area_util_m2: float
    quartos: int
    casas_banho: Optional[int] = None
    freguesia: Optional[str] = None
    concelho: Optional[str] = None
    distrito: Optional[str] = None
    estado: Optional[str] = None
    ano_construcao: Optional[int] = None
    cert_energetico: Optional[str] = None
    tipologia: Optional[str] = None
    source_portal: str
    source_url: str


class ListingCreate(ListingBase):
    """Schema for creating a listing."""
    pass


class ListingResponse(ListingBase):
    """Schema for listing response."""
    id: str
    preco_por_m2: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    scrape_timestamp: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ListingListResponse(BaseModel):
    """Response schema for paginated listings."""
    listings: List[ListingResponse] = Field(..., description="List of listings")
    total: int = Field(..., ge=0, description="Total number of listings")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class ListingFilter(BaseModel):
    """Schema for listing filters."""
    concelho: Optional[str] = None
    distrito: Optional[str] = None
    preco_min: Optional[float] = None
    preco_max: Optional[float] = None
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    quartos_min: Optional[int] = None
    quartos_max: Optional[int] = None
    source_portal: Optional[str] = None
