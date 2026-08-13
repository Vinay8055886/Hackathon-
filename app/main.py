"""Aegis-LLM FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Gauge

from app.api import auth, ci, findings, health, payloads, reports, runs, targets
from app.core.config import get_settings
from app.core.db import get_session_factory, init_db
from app.core.logging import setup_logging
from app.services.bootstrap import bootstrap

logger = logging.getLogger("aegis.main")

runs_started = Counter("aegis_runs_started_total", "Attack runs dispatched")
runs_completed = Counter("aegis_runs_completed_total", "Attack runs completed", ["status"])
findings_total = Counter("aegis_findings_total", "Findings recorded", ["severity"])
active_runs = Gauge("aegis_runs_active", "Runs currently in flight")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(get_settings().log_level)
    # Create tables if they don't exist (demo-friendly). Alembic remains the
    # canonical schema path for real deployments.
    await init_db()
    session_factory = get_session_factory()
    async with session_factory() as session:
        await bootstrap(session)
    logger.info("Aegis-LLM ready (env=%s runner=%s)", get_settings().env, get_settings().runner)
    yield
    from app.core.redis import close_redis

    await close_redis()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Aegis-LLM",
        description=(
            "Safe-by-design, multi-agent LLM red-teaming platform. "
            "Targets must be registered AND allow-listed before any interaction; "
            "every request is rate-limited, budgeted, circuit-broken, and audit-logged."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.is_prod and [] or ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(targets.router)
    app.include_router(payloads.router)
    app.include_router(runs.router)
    app.include_router(findings.router)
    app.include_router(reports.router)
    app.include_router(ci.router)

    if settings.enable_otel:
        _setup_otel(app, settings)

    @app.get("/")
    async def root() -> dict:
        return {
            "service": "aegis-llm",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/healthz",
            "metrics": "/metrics",
        }

    return app


def _setup_otel(app: FastAPI, settings) -> None:
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": "aegis-llm-api"})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint))
        )
        trace.set_tracer_provider(provider)
        logger.info("OpenTelemetry tracing enabled -> %s", settings.otel_exporter_otlp_endpoint)
    except Exception as exc:  # pragma: no cover
        logger.warning("OTel setup failed (%s); continuing without tracing", exc)


app = create_app()
