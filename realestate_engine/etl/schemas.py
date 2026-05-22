"""Pydantic schemas for ETL validation - replaces manual sanitization in pipeline_etl.py."""

from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional
from datetime import datetime


class CleanListingSchema(BaseModel):
    """Schema-driven validation for clean listings. Replaces 54 lines of manual sanitization."""

    source_portal: str = Field(default="unknown", min_length=1, max_length=50)
    source_id: str = Field(default="", min_length=1, max_length=100)
    source_url: str = Field(default="", max_length=500)
    scrape_timestamp: str = Field(default="")

    titulo: Optional[str] = Field(default=None, max_length=500)
    descricao: Optional[str] = Field(default=None, max_length=10000)
    preco_pedido: Optional[float] = Field(default=None, ge=0)
    area_util_m2: Optional[float] = Field(default=None, ge=0)
    area_bruta_m2: Optional[float] = Field(default=None, ge=0)
    quartos: Optional[int] = Field(default=None, ge=0)
    casas_banho: Optional[int] = Field(default=None, ge=0)
    tipologia: Optional[str] = Field(default=None, max_length=20)
    ano_construcao: Optional[int] = Field(default=None, ge=1800, le=2100)
    estado: Optional[str] = Field(default=None, max_length=50)
    certificado_energetico: Optional[str] = Field(default=None, max_length=5)

    freguesia: Optional[str] = Field(default=None, max_length=100)
    concelho: Optional[str] = Field(default=None, max_length=100)
    distrito: Optional[str] = Field(default=None, max_length=100)
    morada: Optional[str] = Field(default=None, max_length=500)
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lon: Optional[float] = Field(default=None, ge=-180, le=180)

    tem_garagem: Optional[bool] = Field(default=None)
    tem_piscina: Optional[bool] = Field(default=None)
    tem_elevador: Optional[bool] = Field(default=None)
    tem_terraco: Optional[bool] = Field(default=None)
    tem_jardim: Optional[bool] = Field(default=None)
    tem_ac: Optional[bool] = Field(default=None)

    fotos: Optional[list] = Field(default=None)
    agencia: Optional[str] = Field(default=None, max_length=200)

    @field_validator("source_portal", mode="before")
    @classmethod
    def sanitize_source_portal(cls, v):
        if not isinstance(v, str):
            v = str(v) if v else "unknown"
        return v.strip()

    @field_validator("source_id", mode="before")
    @classmethod
    def sanitize_source_id(cls, v):
        if not isinstance(v, str):
            v = str(v) if v else ""
        return v.strip()

    @field_validator("source_url", mode="before")
    @classmethod
    def sanitize_source_url(cls, v):
        if not isinstance(v, str):
            v = str(v) if v else ""
        return v.strip()

    @field_validator("preco_pedido", mode="before")
    @classmethod
    def sanitize_price(cls, v):
        if v is None:
            return None
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if v <= 0:
            return None
        return v

    @field_validator("area_util_m2", "area_bruta_m2", mode="before")
    @classmethod
    def sanitize_area(cls, v):
        if v is None:
            return None
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if v <= 0:
            return None
        return v

    @field_validator("quartos", "casas_banho", mode="before")
    @classmethod
    def sanitize_int_field(cls, v):
        if v is None:
            return None
        try:
            v = int(float(v))
        except (TypeError, ValueError):
            return None
        if v < 0:
            return None
        return v

    @field_validator("lat", mode="before")
    @classmethod
    def sanitize_lat(cls, v):
        if v is None:
            return None
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if not (-90 <= v <= 90):
            return None
        return v

    @field_validator("lon", mode="before")
    @classmethod
    def sanitize_lon(cls, v):
        if v is None:
            return None
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if not (-180 <= v <= 180):
            return None
        return v

    @field_validator("ano_construcao", mode="before")
    @classmethod
    def sanitize_year(cls, v):
        if v is None:
            return None
        try:
            v = int(float(v))
        except (TypeError, ValueError):
            return None
        if not (1800 <= v <= 2100):
            return None
        return v

    class Config:
        extra = "ignore"
