"""AI-powered investment opportunity analyzer.

Uses a local LLM (Ollama) to generate an investment thesis for the top
scoring listings, with a deterministic fallback that keeps the dashboard
operational when the LLM is offline or slow.

Production-hardening notes (see PRODUCTION_READINESS.md, fix B3):
- Endpoint and model are env-driven (``OLLAMA_HOST``, ``OLLAMA_MODEL``) so
  the user can switch between mistral:7b, qwen3-14b-fast, qwen3-35b-q4
  without code changes.
- Connect and read timeouts are separated. The first call after a cold
  start of a 7B+ model can easily take 60-180 s on CPU; the previous
  60 s blanket timeout was the root cause of the persistent
  ``{'error': 'timeout'}`` diagnostic.
- ``keep_alive`` keeps the model warm in Ollama between calls.
- One retry with backoff on ReadTimeout (the warm second call usually
  succeeds in under 10 s).
- Successful theses are cached on disk by (listing_id, model) so the
  same deal is never analysed twice.
- Structured logging (model, latency_ms, fallback) so timeouts are
  observable in production.
"""
import os
import json
import time
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from realestate_engine.database.models import CleanListing, Score, Valuation
from realestate_engine.utils.config import config


# ── Module-level configuration (env-driven) ──────────────────────────────
DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b")
# Cold-start of a 7B model on CPU/SSD can exceed 60 s; allow generous read
# timeout but keep connect timeout short so we fail fast when Ollama is down.
CONNECT_TIMEOUT_S = float(os.getenv("OLLAMA_CONNECT_TIMEOUT_S", "5"))
READ_TIMEOUT_S = float(os.getenv("OLLAMA_READ_TIMEOUT_S", "180"))
# Keep model resident in Ollama between calls (string accepted by Ollama).
KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
# How many automatic retries on ReadTimeout (warm calls usually succeed).
MAX_RETRIES = int(os.getenv("OLLAMA_MAX_RETRIES", "1"))
# On-disk cache (so re-opening the dashboard does not re-call the LLM).
CACHE_DIR = Path(os.getenv("AI_DEALS_CACHE_DIR", "data/cache/ai_deals"))
# Cache TTL in hours (default 24h, 0 = never expire)
CACHE_TTL_HOURS = float(os.getenv("AI_DEALS_CACHE_TTL_HOURS", "24"))


def _cache_path(listing_id: int, model: str) -> Path:
    digest = hashlib.sha256(f"{listing_id}::{model}".encode()).hexdigest()[:16]
    return CACHE_DIR / f"{digest}.json"


def _cache_get(listing_id: int, model: str) -> Optional[Dict[str, Any]]:
    """Get cached thesis with TTL check. Returns dict with thesis and timestamp or None."""
    try:
        p = _cache_path(listing_id, model)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            created_at = data.get("created_at")
            # Check TTL if configured
            if CACHE_TTL_HOURS > 0 and created_at:
                from datetime import datetime, timezone
                try:
                    created = datetime.fromisoformat(created_at)
                    age_hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600
                    if age_hours > CACHE_TTL_HOURS:
                        logger.debug(f"AI deals cache expired | listing_id={listing_id} age_hours={age_hours:.1f}")
                        return None
                except Exception:
                    pass  # If timestamp parsing fails, use cache anyway
            return {
                "thesis": data.get("thesis"),
                "created_at": created_at or "unknown"
            }
    except Exception as e:  # pragma: no cover - cache is best-effort
        logger.debug(f"AI deals cache read failed: {e}")
    return None


def _cache_put(listing_id: int, model: str, thesis: str) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        p = _cache_path(listing_id, model)
        from datetime import datetime, timezone
        created_at = datetime.now(timezone.utc).isoformat()
        p.write_text(
            json.dumps({"listing_id": listing_id, "model": model, "thesis": thesis, "created_at": created_at}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:  # pragma: no cover - cache is best-effort
        logger.debug(f"AI deals cache write failed: {e}")


def clear_cache() -> int:
    """Clear all cached theses. Returns number of files deleted."""
    count = 0
    try:
        if CACHE_DIR.exists():
            for f in CACHE_DIR.glob("*.json"):
                try:
                    f.unlink()
                    count += 1
                except Exception:
                    pass
            logger.info(f"AI deals cache cleared | files_deleted={count}")
    except Exception as e:
        logger.warning(f"Failed to clear cache: {e}")
    return count


class OpportunityAnalyzer:
    """Uses AI to analyze and rank the best real estate deals."""

    def __init__(
        self,
        provider: str = "ollama",
        model: Optional[str] = None,
        host: Optional[str] = None,
        use_cache: bool = True,
    ):
        self.provider = provider
        self.model = model or DEFAULT_OLLAMA_MODEL
        self.host = (host or DEFAULT_OLLAMA_HOST).rstrip("/")
        self.use_cache = use_cache
        self.last_source = "unknown"
        self.last_diagnostic: Optional[Dict[str, Any]] = None
        self._warmed_up = False
        
    async def analyze_deal(self, listing: CleanListing, score: Score, valuation: Valuation) -> str:
        """Analyze a single property deal and generate a thesis."""

        preco_por_m2 = listing.preco_por_m2 or (listing.preco_pedido / listing.area_util_m2 if listing.preco_pedido and listing.area_util_m2 else 0)
        valor_justo = valuation.valor_justo or 0
        discount_pct = (valuation.discount or 0) * 100
        score_rationale = score.rationale or "Sem rationale disponível"
        titulo = listing.titulo or "Sem título"
        tipologia = listing.tipologia or "N/D"
        freguesia = listing.freguesia or "N/D"
        concelho = listing.concelho or "N/D"
        estado = listing.estado or "N/D"
        ano_construcao = listing.ano_construcao or "N/D"
        cert_energetico = listing.cert_energetico or "N/D"
        quartos = listing.quartos or 0
        casas_banho = listing.casas_banho or 0

        # Get INE market context
        from realestate_engine.valuation.ine_client import INEClient
        ine = INEClient()
        market_context = ine.get_market_context(freguesia, concelho)
        median_price_m2 = market_context.get("median_price_m2", 0)
        yoy_variation = market_context.get("yoy_variation_pct", 0)
        market_activity = market_context.get("market_activity", "desconhecido")
        monthly_trend = market_context.get("monthly_trend_pct", 0)

        # Build amenities list
        amenities = []
        if listing.tem_garagem: amenities.append("garagem")
        if listing.tem_piscina: amenities.append("piscina")
        if listing.tem_vista_mar: amenities.append("vista mar")
        if listing.tem_vista_rio: amenities.append("vista rio")
        if listing.tem_elevador: amenities.append("elevador")
        if listing.tem_terraco: amenities.append("terraço")
        if listing.tem_jardim: amenities.append("jardim")
        if listing.tem_ac: amenities.append("ar condicionado")
        if listing.cozinha_separada: amenities.append("cozinha separada")
        if listing.tem_aquecimento: amenities.append("aquecimento")

        # Distance to services
        dist_metro = f"{listing.dist_metro_m:.0f}m" if listing.dist_metro_m else "N/D"
        dist_escola = f"{listing.dist_escola_m:.0f}m" if listing.dist_escola_m else "N/D"
        dist_comercio = f"{listing.dist_comercio_m:.0f}m" if listing.dist_comercio_m else "N/D"

        # Prepare context for AI
        prompt = f"""
        Analise este imóvel como um investimento imobiliário no Porto:

        TÍTULO: {titulo}
        TIPOLOGIA: {tipologia} ({quartos} quartos, {casas_banho} casas de banho)
        LOCALIZAÇÃO: {freguesia}, {concelho}
        ÁREA: {listing.area_util_m2 or 0} m2
        PREÇO PEDIDO: {(listing.preco_pedido or 0):,.0f}€
        PREÇO/M2: {preco_por_m2:,.0f}€/m2
        VALOR DE MERCADO ESTIMADO: {valor_justo:,.0f}€
        DESCONTO: {discount_pct:.1f}%
        ESTADO: {estado}
        ANO CONSTRUÇÃO: {ano_construcao}
        CERTIFICAÇÃO ENERGÉTICA: {cert_energetico}
        SCORE DO SISTEMA: {score.score_total}/10
        FACTORES DE SCORE: {score_rationale}

        CONTEXTO DE MERCADO (INE):
        - Preço médio/m² na zona: {median_price_m2:,.0f}€
        - Comparação: imóvel está {((preco_por_m2/median_price_m2 - 1)*100):+.1f}% vs média da zona
        - Tendência anual: {yoy_variation:+.1f}% ({'crescente' if yoy_variation > 0 else 'descendente' if yoy_variation < 0 else 'estável'})
        - Atividade de mercado: {market_activity}
        - Tendência mensal: {monthly_trend:+.2f}%

        AMENITIES: {', '.join(amenities) if amenities else 'Nenhuma destacada'}
        DISTÂNCIAS: Metro {dist_metro}, Escola {dist_escola}, Comércio {dist_comercio}

        Com base nestes dados, escreva uma tese de investimento curta (máximo 4 parágrafos) em Português.
        Destaque o potencial de valorização, riscos e se é uma boa oportunidade para "Buy-to-Let" ou "Fix-and-Flip".
        Considere o contexto de mercado (preço vs média da zona, tendência) e as amenities disponíveis.
        """
        
        if not await self._check_ollama_status():
            raise ValueError("Ollama not available")
        
        if self.provider == "ollama":
            return await self._call_ollama(prompt, listing, score, valuation)
        else:
            self.last_source = "fallback_local"
            self.last_diagnostic = {"reason": "provider_not_implemented"}
            return self._build_local_fallback_thesis(listing, score, valuation, "provider not implemented")

    async def _warm_up(self, client) -> Tuple[bool, Optional[str]]:
        """Pre-load the model so the first real prompt isn't a cold-start.

        Sends a 1-token generate request which forces Ollama to load the
        model weights into memory. Subsequent calls (within ``keep_alive``)
        return in seconds rather than minutes.
        Returns (ok, error_message).
        """
        if self._warmed_up:
            return True, None
        t0 = time.perf_counter()
        try:
            r = await client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": "ok",
                    "stream": False,
                    "keep_alive": KEEP_ALIVE,
                    "options": {"num_predict": 1},
                },
            )
            ms = int((time.perf_counter() - t0) * 1000)
            if r.status_code == 200:
                self._warmed_up = True
                logger.info(
                    f"Ollama warm-up ok | model={self.model} latency_ms={ms}"
                )
                return True, None
            if r.status_code == 404:
                msg = (
                    f"Modelo '{self.model}' não encontrado em {self.host}. "
                    f"Corre: ollama pull {self.model}"
                )
                logger.error(msg)
                return False, msg
            return False, f"Ollama warm-up status {r.status_code}"
        except Exception as e:
            return False, f"warm-up exception: {e.__class__.__name__}: {e}"

    async def _call_ollama(self, prompt: str, listing: CleanListing, score: Score, valuation: Valuation) -> str:
        """Call local Ollama with warm-up, retry, and separated timeouts."""
        import httpx

        timeout = httpx.Timeout(connect=CONNECT_TIMEOUT_S, read=READ_TIMEOUT_S, write=10.0, pool=5.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            # Warm-up first so the cold-start latency doesn't blow our timeout.
            warm_ok, warm_err = await self._warm_up(client)
            if not warm_ok:
                self.last_source = "fallback_local"
                self.last_diagnostic = {"error": "warm_up_failed", "detail": warm_err, "model": self.model, "host": self.host}
                logger.warning(f"Ollama unavailable, using fallback | reason={warm_err}")
                return self._build_local_fallback_thesis(listing, score, valuation, warm_err or "Ollama indisponível")

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": KEEP_ALIVE,
            }

            last_exc: Optional[Exception] = None
            for attempt in range(MAX_RETRIES + 1):
                t0 = time.perf_counter()
                try:
                    r = await client.post(f"{self.host}/api/generate", json=payload)
                    ms = int((time.perf_counter() - t0) * 1000)
                    if r.status_code == 200:
                        self.last_source = "ollama"
                        self.last_diagnostic = {
                            "status_code": 200,
                            "model": self.model,
                            "host": self.host,
                            "latency_ms": ms,
                            "attempt": attempt + 1,
                        }
                        logger.info(
                            f"Ollama generate ok | model={self.model} latency_ms={ms} attempt={attempt + 1}"
                        )
                        return r.json().get("response", "Erro na resposta da IA")
                    # Non-200: don't retry, fall through to fallback.
                    self.last_source = "fallback_local"
                    self.last_diagnostic = {
                        "status_code": r.status_code,
                        "model": self.model,
                        "host": self.host,
                        "latency_ms": ms,
                    }
                    logger.warning(
                        f"Ollama non-200 | status={r.status_code} latency_ms={ms}"
                    )
                    return self._build_local_fallback_thesis(
                        listing, score, valuation, f"Ollama respondeu com status {r.status_code}",
                    )
                except httpx.ConnectError as e:
                    # Connect errors aren't worth retrying inside the same call.
                    logger.error(f"Ollama connect error | host={self.host} err={e}")
                    self.last_source = "fallback_local"
                    self.last_diagnostic = {"error": "connect_error", "detail": str(e), "host": self.host}
                    return self._build_local_fallback_thesis(
                        listing, score, valuation, f"Ollama não está acessível em {self.host}",
                    )
                except httpx.ReadTimeout as e:
                    last_exc = e
                    ms = int((time.perf_counter() - t0) * 1000)
                    logger.warning(
                        f"Ollama timeout | model={self.model} latency_ms={ms} attempt={attempt + 1}/{MAX_RETRIES + 1}"
                    )
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(2.0 * (attempt + 1))
                        continue
                except Exception as e:  # pragma: no cover - defensive
                    last_exc = e
                    logger.error(f"Ollama unexpected error | err={e.__class__.__name__}: {e}")
                    break

            # All retries exhausted.
            self.last_source = "fallback_local"
            self.last_diagnostic = {
                "error": "timeout" if isinstance(last_exc, httpx.ReadTimeout) else "unexpected",
                "detail": str(last_exc) if last_exc else "unknown",
                "model": self.model,
                "host": self.host,
                "attempts": MAX_RETRIES + 1,
            }
            return self._build_local_fallback_thesis(
                listing, score, valuation,
                f"timeout após {MAX_RETRIES + 1} tentativas (read_timeout={READ_TIMEOUT_S}s)",
            )

    def _build_local_fallback_thesis(self, listing: CleanListing, score: Score, valuation: Valuation, reason: str) -> str:
        """Build a professional local thesis when the LLM is unavailable.

        The fallback keeps the dashboard operational and explains the commercial
        rationale using deterministic rules so the user can still trust the output.
        Uses varied templates to avoid repetitive output.
        """
        import random
        
        price = listing.preco_pedido or 0
        fair_value = valuation.valor_justo or 0
        discount_pct = ((fair_value - price) / price * 100) if price else 0
        confidence = (valuation.confianca or 0) * 100
        city = listing.concelho or "mercado"
        area = f"{listing.area_util_m2:.0f} m²" if listing.area_util_m2 else "área não informada"
        tipologia = listing.tipologia or "Imóvel"
        estado = listing.estado or "estado não especificado"
        freguesia = listing.freguesia or "zona"
        quartos = listing.quartos or 0
        casas_banho = listing.casas_banho or 0
        
        # Get INE market context
        from realestate_engine.valuation.ine_client import INEClient
        ine = INEClient()
        market_context = ine.get_market_context(freguesia, city)
        median_price_m2 = market_context.get("median_price_m2", 0)
        yoy_variation = market_context.get("yoy_variation_pct", 0)
        market_activity = market_context.get("market_activity", "desconhecido")
        
        preco_por_m2 = listing.preco_por_m2 or (price / listing.area_util_m2 if listing.area_util_m2 else 0)
        vs_median_pct = ((preco_por_m2 / median_price_m2 - 1) * 100) if median_price_m2 > 0 else 0
        
        # Build amenities list
        amenities = []
        if listing.tem_garagem: amenities.append("garagem")
        if listing.tem_piscina: amenities.append("piscina")
        if listing.tem_vista_mar: amenities.append("vista mar")
        if listing.tem_vista_rio: amenities.append("vista rio")
        if listing.tem_elevador: amenities.append("elevador")
        if listing.tem_terraco: amenities.append("terraço")
        if listing.tem_jardim: amenities.append("jardim")
        if listing.tem_ac: amenities.append("ar condicionado")
        
        # Use listing_id as seed for deterministic but varied output per listing
        random.seed(listing.id if hasattr(listing, 'id') else 0)
        
        # Template variations for opening
        openings = [
            f"⚠️ *Fallback local ativado* — {reason}.",
            f"⚠️ Análise gerada localmente (IA indisponível: {reason}).",
            f"ℹ️ Modo fallback ativo — {reason}.",
        ]
        
        # Template variations for context with market data
        contexts = [
            f"Este {tipologia} ({quartos} quartos, {casas_banho} wcs) em {freguesia}, {city}, tem {area} e score {score.score_total:.1f}/10. Preço/m² está {vs_median_pct:+.1f}% vs média da zona ({median_price_m2:,.0f}€/m²).",
            f"Localizado em {freguesia} ({city}), este {tipologia} de {area} apresenta valuation de {fair_value:,.0f}€ e score {score.score_total:.1f}/10. Mercado local está {market_activity} com tendência anual de {yoy_variation:+.1f}%.",
            f"Com {area} em {freguesia}, {city}, o imóvel tem preço/m² de {preco_por_m2:,.0f}€ vs média da zona de {median_price_m2:,.0f}€/m² ({vs_median_pct:+.1f}%). Score do sistema: {score.score_total:.1f}/10.",
        ]
        
        # Template variations for price analysis with market context
        if discount_pct > 10:
            price_analysis = [
                f"Desconto significativo de {discount_pct:.1f}% face ao valor justo. Com mercado em tendência {('crescente' if yoy_variation > 0 else 'descendente' if yoy_variation < 0 else 'estável')}, a margem de segurança é atrativa para investimento.",
                f"Preço pedido {price:,.0f}€ vs valor justo {fair_value:,.0f}€ (desconto {discount_pct:.1f}%). Preço/m² {vs_median_pct:+.1f}% vs média da zona em mercado {market_activity}.",
                f"A diferença de {discount_pct:.1f}% entre preço e valor justo, combinada com preço/m² {vs_median_pct:+.1f}% vs média, indica oportunidade de entrada com boa margem.",
            ]
        elif discount_pct > 0:
            price_analysis = [
                f"Desconto moderado de {discount_pct:.1f}% com preço/m² {vs_median_pct:+.1f}% vs média da zona. Margem depende de confirmação do estado e localização.",
                f"Preço ligeiramente abaixo do valor justo ({discount_pct:.1f}%) e {vs_median_pct:+.1f}% vs média da zona em mercado {market_activity}. Válido se estado for confirmado.",
            ]
        else:
            price_analysis = [
                f"Preço próximo do valor justo e {vs_median_pct:+.1f}% vs média da zona. Potencial depende de valorização de mercado (tendência {yoy_variation:+.1f}% anual) e execução operacional.",
                f"Sem margem de desconto significativa. Preço/m² {vs_median_pct:+.1f}% vs média em mercado {market_activity}. Investimento depende de valorização futura.",
            ]
        
        # Template variations for amenities analysis
        if amenities:
            amenities_text = f"Amenidades destacadas: {', '.join(amenities)}."
            amenities_analysis = [
                f"{amenities_text} Estas características podem justificar prémio no preço e atrair inquilinos de qualidade.",
                f"{amenities_text} Fatores positivos para yield potencial e valorização a longo prazo.",
            ]
        else:
            amenities_analysis = [
                "Sem amenities destacadas. Potencial de valorização depende mais de localização e estado físico.",
                "Amenidades básicas. Considerar custo de melhorias para aumentar atratividade.",
            ]
        
        # Template variations for strategy
        strategies = [
            f"Estratégia: validar estado ({estado.lower()}), confirmar comparáveis em {freguesia}, e avaliar potencial de renda (buy-to-let) ou revenda. Mercado local {market_activity}.",
            f"Próximos passos: visita técnica, análise de comparáveis na zona, e cálculo de yield. Considerar tendência de mercado ({yoy_variation:+.1f}% anual).",
            f"Para decisão: confirmar localização em {freguesia}, verificar estado real ({estado.lower()}), e confrontar com transações recentes. Mercado {market_activity}.",
        ]
        
        # Template variations for risks
        risks = [
            "Risco: usar apenas esta análise sem validação presencial. Confirmar com visita e comparáveis atualizados.",
            "Atenção: análise baseada em dados automatizados. Decisão final requer due diligence completa.",
            "Nota: validar estado físico, documentação e contexto urbanístico local antes de avançar.",
        ]
        
        # Select one from each category
        thesis_lines = [
            random.choice(openings),
            random.choice(contexts),
            random.choice(price_analysis),
            random.choice(amenities_analysis),
            random.choice(strategies),
            random.choice(risks),
        ]
        
        # Add freshness marker
        from datetime import datetime
        thesis_lines.append(f"\n*Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        
        return "\n\n".join(thesis_lines)

    async def get_top_deals_report(self, limit: int = 5, force_refresh: bool = False, 
                                  freguesia: Optional[str] = None, tipologia: Optional[str] = None,
                                  min_price: Optional[float] = None, max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """Analyze the top N deals from the database.
        
        Args:
            limit: Number of top deals to analyze
            force_refresh: If True, ignore cache and re-analyze all deals
            freguesia: Filter by freguesia (optional)
            tipologia: Filter by tipologia (optional)
            min_price: Minimum price filter (optional)
            max_price: Maximum price filter (optional)
        """
        from realestate_engine.database.repository import DatabaseRepository
        from sqlalchemy import and_, select
        repo = DatabaseRepository()
        
        # Get top scoring listings with valuations and optional filters
        min_score = 6.0
        
        # Build filter conditions
        filters = [Score.score_total >= min_score]
        if freguesia:
            filters.append(CleanListing.freguesia.ilike(f"%{freguesia}%"))
        if tipologia:
            filters.append(CleanListing.tipologia.ilike(f"%{tipologia}%"))
        if min_price:
            filters.append(CleanListing.preco_pedido >= min_price)
        if max_price:
            filters.append(CleanListing.preco_pedido <= max_price)
        
        from sqlalchemy.orm import joinedload
        with repo.Session() as session:
            query = select(Score).options(
                joinedload(Score.listing).options(joinedload(CleanListing.valuations))
            ).join(Score.listing).where(and_(*filters))
            
            # Filter out sample data
            query = query.where(CleanListing.is_sample == 0)
            
            query = query.order_by(Score.score_total.desc()).limit(limit * 2)  # Get more to filter after
            top_scores = list(session.execute(query).unique().scalars().all())
        
        results = []
        for score in top_scores:
            listing = score.listing
            valuation = listing.valuations[0] if listing and getattr(listing, "valuations", None) else None
            
            if not valuation:
                continue
            
            cached_data = None
            created_at = None
            
            if not force_refresh and self.use_cache:
                cached_data = _cache_get(listing.id, self.model)
            
            if cached_data is not None:
                thesis = cached_data["thesis"]
                created_at = cached_data.get("created_at")
                self.last_source = "ollama_cache"
                self.last_diagnostic = {
                    "cache_hit": True, 
                    "model": self.model, 
                    "listing_id": listing.id,
                    "created_at": created_at
                }
                logger.debug(f"AI deals cache hit | listing_id={listing.id} model={self.model} created_at={created_at}")
            else:
                try:
                    thesis = await self.analyze_deal(listing, score, valuation)
                    created_at = None  # Fresh analysis
                except Exception as e:
                    logger.error(f"Failed to analyze deal {getattr(listing, 'id', 'unknown')}: {e}")
                    self.last_source = "fallback_local"
                    self.last_diagnostic = {"error": "analysis_failure", "detail": str(e)}
                    thesis = self._build_local_fallback_thesis(listing, score, valuation, f"falha na análise IA: {e}")
                    created_at = None
                # Only cache successful Ollama responses, not fallbacks.
                if self.use_cache and self.last_source == "ollama":
                    _cache_put(listing.id, self.model, thesis)
            
            # Add market context to results
            from realestate_engine.valuation.ine_client import INEClient
            ine = INEClient()
            market_context = ine.get_market_context(listing.freguesia, listing.concelho)
            
            results.append({
                "listing_id": listing.id,
                "title": listing.titulo,
                "score": score.score_total,
                "discount": valuation.discount,
                "thesis": thesis,
                "url": listing.source_url,
                "analysis_source": self.last_source,
                "analysis_diagnostic": self.last_diagnostic,
                "created_at": created_at,
                "freguesia": listing.freguesia,
                "concelho": listing.concelho,
                "preco_pedido": listing.preco_pedido,
                "preco_por_m2": listing.preco_por_m2,
                "median_price_m2": market_context.get("median_price_m2"),
                "yoy_variation": market_context.get("yoy_variation_pct"),
                "market_activity": market_context.get("market_activity"),
            })
            
            # Stop when we have enough results
            if len(results) >= limit:
                break
            
        return results

    async def _check_ollama_status(self):
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                r = await client.head(f'{self.host}/api/version', timeout=5)
                return r.status_code == 200
        except Exception:
            return False
