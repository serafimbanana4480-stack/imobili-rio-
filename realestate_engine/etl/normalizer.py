"""Normalizer for converting raw listings to clean format."""
import re
from typing import Dict, Any, Optional
from loguru import logger


class Normalizer:
    """Normalizes raw listing data into canonical format."""
    
    @staticmethod
    def normalize_price(price_text: Optional[str]) -> Optional[float]:
        """Extract numeric price from text, handling EU and US formats."""
        if not price_text:
            return None
        
        text = str(price_text).strip()
        
        # Handle "k" notation (250k -> 250000, 1.5M -> 1500000)
        k_match = re.search(r"([\d.,]+)\s*[kK]", text)
        if k_match:
            try:
                return float(k_match.group(1).replace(",", ".")) * 1000
            except ValueError:
                pass
        
        m_match = re.search(r"([\d.,]+)\s*[mM]", text)
        if m_match:
            try:
                return float(m_match.group(1).replace(",", ".")) * 1_000_000
            except ValueError:
                pass
        
        # Remove unit suffixes (m2, €, EUR, etc.)
        text = re.sub(r"(?i)\s*(m2|sqm|€|EUR|euros?)\s*", "", text)
        
        # Remove spaces between digits (300 000 -> 300000)
        text = re.sub(r"(\d)\s+(\d)", r"\1\2", text)
        
        # Remove other non-numeric chars except . and ,
        cleaned = re.sub(r"[^\d.,]", "", text)
        
        if not cleaned:
            return None
            
        # If both . and , are present
        if "." in cleaned and "," in cleaned:
            if cleaned.rfind(".") > cleaned.rfind(","):
                # US: 1,234.56
                cleaned = cleaned.replace(",", "")
            else:
                # EU: 1.234,56
                cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            # Only comma: could be 1,234 (thousand) or 12,34 (decimal)
            parts = cleaned.split(",")
            if len(parts[-1]) == 3 and len(parts) > 1:
                # Likely thousand separator (1,234 or 1,234,567)
                cleaned = cleaned.replace(",", "")
            elif len(parts[-1]) <= 2:
                # Likely decimal
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "." in cleaned:
            # Only dot: could be 1.234 (thousand) or 12.34 (decimal)
            parts = cleaned.split(".")
            if len(parts[-1]) == 3 and len(parts) > 1:
                # Likely thousand separator (1.234 or 1.234.567)
                cleaned = cleaned.replace(".", "")
            elif len(parts[-1]) <= 2 and len(parts) == 2:
                # Likely decimal (85.5 or 1234.56)
                pass
            else:
                cleaned = cleaned.replace(".", "")
        
        try:
            value = float(cleaned)
            # Sanity check: reject nonsensical values
            if value < 1:
                return None
            return value
        except ValueError:
            return None
    
    @staticmethod
    def normalize_area(area_text: Optional[str]) -> Optional[float]:
        """Extract numeric area from text. Areas are always small numbers (10-2000 m²)."""
        if not area_text:
            return None
        
        text = str(area_text).strip()
        
        # Remove m², sqm, etc.
        text = re.sub(r"(?i)\s*(m2|m²|sqm|sq\.?\s*m)\s*", "", text)
        
        # Remove spaces between digits
        text = re.sub(r"(\d)\s+(\d)", r"\1\2", text)
        
        # Remove non-numeric except . and ,
        cleaned = re.sub(r"[^\d.,]", "", text)
        if not cleaned:
            return None
        
        # For areas, comma is almost always decimal (82,5 m²)
        if "," in cleaned and "." not in cleaned:
            cleaned = cleaned.replace(",", ".")
        elif "." in cleaned and "," in cleaned:
            # EU format: remove dots, replace comma with dot
            cleaned = cleaned.replace(".", "").replace(",", ".")
        
        try:
            value = float(cleaned)
            # Sanity: areas between 5 and 10000 m²
            if value < 5 or value > 10000:
                return None
            return value
        except ValueError:
            return None
    
    @staticmethod
    def normalize_rooms(rooms_text: Optional[str]) -> Optional[int]:
        """Extract number of rooms from text."""
        if not rooms_text:
            return None
        match = re.search(r"(\d+)", str(rooms_text))
        return int(match.group(1)) if match else None
    
    @staticmethod
    def normalize_bathrooms(bath_text: Optional[str]) -> Optional[int]:
        """Extract number of bathrooms from text."""
        return Normalizer.normalize_rooms(bath_text)
    
    @staticmethod
    def normalize_tipologia(title: Optional[str], description: Optional[str] = None) -> Optional[str]:
        """Extract property typology from text and canonicalise to T0, T1, T2, etc."""
        text = f"{title or ''} {description or ''}"
        patterns = [
            r"(T\d+)",
            r"(\d+)\s*(?:quartos?|bedrooms?)",
            r"(studio|loft|duplex|moradia|apartamento|casa)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw = match.group(1).upper()
                # Canonical mapping
                canonical = {
                    "STUDIO": "T0",
                    "LOFT": "T0",
                    "DUPLEX": "T2",
                    "MORADIA": "T5+",
                    "APARTAMENTO": None,  # too generic; keep searching
                    "CASA": "T5+",
                }.get(raw)
                if canonical:
                    return canonical
                # If it already looks like T\d, return it
                if raw.startswith("T") and raw[1:].isdigit():
                    return raw
                # If it is a digit (rooms count), map to T{rooms}
                if raw.isdigit():
                    return f"T{raw}"
        return None
    
    @staticmethod
    def normalize_estado(text: Optional[str], title: Optional[str] = None, description: Optional[str] = None) -> Optional[str]:
        """Normalize condition/state from text, title, or description."""
        combined = " ".join(filter(None, [text, title, description])).lower()
        if not combined:
            return None
        if any(w in combined for w in ["novo", "new", "construcao", "construction"]):
            return "novo"
        elif any(w in combined for w in ["renovado", "remodelado", "renovated", "remodeled"]):
            return "renovado"
        elif any(w in combined for w in ["bom", "good", "usado"]):
            return "bom"
        elif any(w in combined for w in ["para recuperar", "ruina", "ruin", "recuperar"]):
            return "para_recuperar"
        return None
    
    @classmethod
    def normalize(cls, raw_data: Dict[str, Any], portal: str = "unknown") -> Dict[str, Any]:
        """Normalize raw listing data."""
        normalized = {
            "titulo": raw_data.get("title", "") or raw_data.get("titulo", ""),
            "descricao": raw_data.get("description", "") or raw_data.get("descricao", ""),
            "preco_pedido": cls.normalize_price(raw_data.get("price_text") or raw_data.get("preco") or raw_data.get("price")),
            "area_util_m2": cls.normalize_area(raw_data.get("area_text") or raw_data.get("area") or raw_data.get("area_util")),
            "quartos": cls.normalize_rooms(raw_data.get("rooms") or raw_data.get("rooms_text") or raw_data.get("quartos") or raw_data.get("bedrooms")),
            "casas_banho": cls.normalize_bathrooms(raw_data.get("bathrooms") or raw_data.get("bathrooms_text") or raw_data.get("casas_banho") or raw_data.get("bathrooms")),
            "morada_raw": raw_data.get("address", "") or raw_data.get("morada", "") or raw_data.get("location", ""),
            "freguesia": raw_data.get("freguesia", "") or raw_data.get("parish", ""),
            "concelho": raw_data.get("concelho", "") or raw_data.get("municipality", ""),
            "distrito": raw_data.get("distrito", "") or raw_data.get("district", ""),
            "estado": cls.normalize_estado(
                raw_data.get("condition", "") or raw_data.get("estado", ""),
                raw_data.get("title", ""),
                raw_data.get("description", "")
            ),
            "ano_construcao": cls.normalize_rooms(raw_data.get("year_built", "") or raw_data.get("ano_construcao", "")),
            "cert_energetico": raw_data.get("energy_cert", "") or raw_data.get("cert_energetico", ""),
            "tipologia": cls.normalize_tipologia(raw_data.get("title"), raw_data.get("description")),
            "fotos_urls": raw_data.get("photos", []) or raw_data.get("fotos", []) or [],
            "num_fotos": len(raw_data.get("photos", []) or raw_data.get("fotos", []) or []),
            "agencia": raw_data.get("agency", "") or raw_data.get("agencia", ""),
            "source_url": raw_data.get("url", "") or raw_data.get("source_url", ""),
            "source_id": raw_data.get("source_id", "") or str(raw_data.get("id", "")),
            "source_portal": portal,
        }
        
        # Calculate price per m2
        if normalized["preco_pedido"] and normalized["area_util_m2"] and normalized["area_util_m2"] > 0:
            normalized["preco_por_m2"] = normalized["preco_pedido"] / normalized["area_util_m2"]
        
        return normalized
