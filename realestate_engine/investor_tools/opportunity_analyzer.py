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


def _cache_path(listing_id: int, model: str) -> Path:
    digest = hashlib.sha256(f"{listing_id}::{model}".encode()).hexdigest()[:16]
    return CACHE_DIR / f"{digest}.json"


def _cache_get(listing_id: int, model: str) -> Optional[str]:
    try:
        p = _cache_path(listing_id, model)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            return data.get("thesis")
    except Exception as e:  # pragma: no cover - cache is best-effort
        logger.debug(f"AI deals cache read failed: {e}")
    return None


def _cache_put(listing_id: int, model: str, thesis: str) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        p = _cache_path(listing_id, model)
        p.write_text(
            json.dumps({"listing_id": listing_id, "model": model, "thesis": thesis}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:  # pragma: no cover - cache is best-effort
        logger.debug(f"AI deals cache write failed: {e}")


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
        # Read from DB config first, then fall back to env defaults
        db_model = None
        db_host = None
        try:
            from realestate_engine.database.repository import DatabaseRepository
            repo = DatabaseRepository()
            db_model = repo.get_config("ollama_model")
            db_host = repo.get_config("ollama_host")
        except Exception:
            pass
        self.model = model or db_model or DEFAULT_OLLAMA_MODEL
        self.host = (host or db_host or DEFAULT_OLLAMA_HOST).rstrip("/")
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

        # Prepare context for AI
        prompt = f"""
        Analise este imóvel como um investimento imobiliário no Porto:
        
        TÍTULO: {titulo}
        TIPOLOGIA: {tipologia}
        LOCALIZAÇÃO: {freguesia}, {concelho}
        ÁREA: {listing.area_util_m2 or 0} m2
        PREÇO PEDIDO: {(listing.preco_pedido or 0):,.0f}€
        PREÇO/M2: {preco_por_m2:,.0f}€/m2
        VALOR DE MERCADO ESTIMADO: {valor_justo:,.0f}€
        DESCONTO: {discount_pct:.1f}%
        ESTADO: {estado}
        SCORE DO SISTEMA: {score.score_total}/10
        FACTORES DE SCORE: {score_rationale}
        
        Com base nestes dados, escreva uma tese de investimento curta (máximo 4 parágrafos) em Português. 
        Destaque o potencial de valorização, riscos e se é uma boa oportunidade para "Buy-to-Let" ou "Fix-and-Flip".
        """
        
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
        """
        price = listing.preco_pedido or 0
        fair_value = valuation.valor_justo or 0
        discount_pct = ((fair_value - price) / price * 100) if price else 0
        confidence = (valuation.confianca or 0) * 100
        city = listing.concelho or "mercado"
        area = f"{listing.area_util_m2:.0f} m²" if listing.area_util_m2 else "área não informada"
        thesis_lines = [
            f"⚠️ *Fallback local ativado* — {reason}.",
            f"O imóvel em {city} tem um perfil de investimento suportado pelo score do sistema ({score.score_total:.1f}/10) e por um valuation estimado em {fair_value:,.0f}€.",
            f"Com {area}, preço pedido de {price:,.0f}€ e confiança estimada de {confidence:.0f}%, a tese é mais adequada para decisão disciplinada do que para aposta agressiva.",
        ]
        if discount_pct > 0:
            thesis_lines.append(
                f"Existe desconto implícito de aproximadamente {discount_pct:.1f}% face ao valor justo, o que sustenta leitura positiva para buy-to-let se a localização e o estado forem confirmados."
            )
        else:
            thesis_lines.append(
                "O preço pedido já está próximo ou acima do valor justo, pelo que o potencial de valorização depende mais de execução operacional do que de desconto de entrada."
            )
        thesis_lines.append("Risco principal: tratar esta leitura como referência comercial e validar com comparáveis e visita técnica antes de avançar.")
        return "\n\n".join(thesis_lines)

    async def get_top_deals_report(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Analyze the top N deals from the database."""
        from realestate_engine.database.repository import DatabaseRepository
        repo = DatabaseRepository()
        
        # Get top scoring listings with valuations
        top_scores = repo.get_top_scores(min_score=7.5, limit=limit)
        
        results = []
        for score in top_scores:
            listing = score.listing
            valuation = listing.valuations[0] if listing and getattr(listing, "valuations", None) else None
            
            if not valuation:
                continue
                
            cached = _cache_get(listing.id, self.model) if self.use_cache else None
            if cached is not None:
                thesis = cached
                self.last_source = "ollama_cache"
                self.last_diagnostic = {"cache_hit": True, "model": self.model, "listing_id": listing.id}
                logger.debug(f"AI deals cache hit | listing_id={listing.id} model={self.model}")
            else:
                try:
                    thesis = await self.analyze_deal(listing, score, valuation)
                except Exception as e:
                    logger.error(f"Failed to analyze deal {getattr(listing, 'id', 'unknown')}: {e}")
                    self.last_source = "fallback_local"
                    self.last_diagnostic = {"error": "analysis_failure", "detail": str(e)}
                    thesis = self._build_local_fallback_thesis(listing, score, valuation, f"falha na análise IA: {e}")
                # Only cache successful Ollama responses, not fallbacks.
                if self.use_cache and self.last_source == "ollama":
                    _cache_put(listing.id, self.model, thesis)
            results.append({
                "listing_id": listing.id,
                "title": listing.titulo,
                "score": score.score_total,
                "discount": valuation.discount,
                "thesis": thesis,
                "url": listing.source_url,
                "analysis_source": self.last_source,
                "analysis_diagnostic": self.last_diagnostic,
            })
            
        return results
