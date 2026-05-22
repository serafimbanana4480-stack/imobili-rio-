"""Pydantic schemas for valuation API."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ValuationRequest(BaseModel):
    """Schema for valuation request."""
    preco_pedido: float = Field(..., gt=0, description="Asking price")
    area_util_m2: float = Field(..., gt=0, description="Usable area in m²")
    quartos: int = Field(..., gt=0, description="Number of bedrooms")
    casas_banho: Optional[int] = Field(None, ge=0, description="Number of bathrooms")
    freguesia: Optional[str] = Field(None, description="Parish")
    concelho: Optional[str] = Field(None, description="Municipality")
    distrito: Optional[str] = Field(None, description="District")
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    lon: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    estado: Optional[str] = Field(None, description="Property condition")
    ano_construcao: Optional[int] = Field(None, ge=1800, le=2100, description="Construction year")
    cert_energetico: Optional[str] = Field(None, description="Energy certificate")
    tipologia: Optional[str] = Field(None, description="Property type")


class ValuationResponse(BaseModel):
    """Schema for valuation response."""
    valor_justo: float = Field(..., description="Fair market value")
    ci_lower: float = Field(..., description="Confidence interval lower bound")
    ci_upper: float = Field(..., description="Confidence interval upper bound")
    confianca: float = Field(..., ge=0, le=1, description="Confidence score")
    discount: Optional[float] = Field(None, description="Discount percentage")
    valuation_quality: Optional[Dict[str, Any]] = Field(None, description="Commercial valuation quality summary")
    value_risk: Optional[Dict[str, Any]] = Field(None, description="Commercial risk label for the valuation")
    
    # Individual model predictions
    hedonic_value: Optional[float] = Field(None, description="Hedonic model value")
    comps_value: Optional[float] = Field(None, description="Comparables value")
    ine_value: Optional[float] = Field(None, description="INE model value")
    xgboost_value: Optional[float] = Field(None, description="XGBoost model value")
    xgboost_explanation: Optional[Dict[str, Any]] = Field(None, description="XGBoost SHAP explanation")
    
    # Ensemble metadata
    ensemble_weights: Optional[Dict[str, float]] = Field(None, description="Model ensemble weights")
    models_active: Optional[int] = Field(None, description="Number of active models")
    
    # Market context
    market_context: Optional[Dict[str, Any]] = Field(None, description="Market context from INE")


class AdvancedValuationResponse(ValuationResponse):
    """Schema for advanced valuation with 8-model ensemble."""
    neural_network_value: Optional[float] = Field(None, description="Neural network value")
    catboost_value: Optional[float] = Field(None, description="CatBoost value")
    random_forest_value: Optional[float] = Field(None, description="Random forest value")
    linear_model_value: Optional[float] = Field(None, description="Linear model value")
    
    individual_predictions: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="All model predictions")
    ensemble_performance: Optional[Dict[str, float]] = Field(None, description="Ensemble performance metrics")
    meta_features: Optional[Dict[str, Any]] = Field(None, description="Meta-learning features")
