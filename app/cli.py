"""Aegis-LLM command-line interface.

Commands:
  init-db                create tables + seed roles/admin/packs
  register-target        register a target and allow-list it
  allowlist-target       allow-list / de-list an existing target
  list-targets           list registered targets
  list-packs             list payload packs + payload counts
  run                    launch an attack run (--dry-run supported)
  findings               list findings (filter by severity/category)
  report                 generate an HTML/SARIF/JSON report
  demo                   end-to-end demo against the bundled mock target

Examples:
  python -m app.cli init-db
  python -m app.cli register-target --name acme-chat --connector-type rest \
      --endpoint http://127.0.0.1:8100/chat --config '{"response_path": "reply"}'
  python -m app.cli run --target <id> --packs prompt-injection,jailbreak,data-exfiltration --dry-run
  python -m app.cli run --target <id> --packs prompt-injection,jailbreak,data-exfiltration
  python -m app.cli report --run <id> --format sarif
  python -m app.cli demo
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from app.core.config import get_settings
from app.core.db import get_session_factory, init_db


# ── helpers ─────────────────────────────────────────────────────────────────
async def _admin_user(session):
    from sqlalchemy import select

    from app.models import User

    settings = get_settings()
    user = (
        await session.execute(
            select(User).where(User.username == settings.admin_username)
        )
    ).scalar_one_or_none()
    if user is None:
        raise SystemExit(
            "Admin user not found — run `python -m app.cli init-db` first"
        )
    return user


async def _resolve_packs(session, names: list[str]) -> list[str]:
    from sqlalchemy import select

    from app.models import PayloadPack

    packs: list[str] = []
    for name in names:
        pack = (
            await session.execute(select(PayloadPack).where(PayloadPack.name == name))
        ).scalar_one_or_none()
        if pack is None:
            raise SystemExit(f"Payload pack {name!r} not found (see `list-packs`)")
        packs.append(pack.id)
    return packs


# ── commands ────────────────────────────────────────────────────────────────
async def cmd_init_db(args: argparse.Namespace) -> None:
    from app.services.bootstrap import bootstrap

    await init_db()
    async with get_session_factory()() as session:
        await bootstrap(session)
    print("Database initialised: tables created, roles + admin user + bundled packs seeded.")


async def cmd_register_target(args: argparse.Namespace) -> None:
    from app.models import Target

    await init_db(create_all=False)
    async with get_session_factory()() as session:
        user = await _admin_user(session)
        target = Target(
            name=args.name,
            description=args.description or "",
            connector_type=args.connector_type,
            endpoint=args.endpoint,
            config=json.loads(args.config) if args.config else {},
            owner_id=user.id,
            allowlisted=False,
        )
        session.add(target)
        await session.flush()
        target.allowlisted = True
        target.approved_by = args.approved_by or user.username
        target.approval_note = args.approval_note or "Registered via CLI"
        await session.commit()
        print(
            f"Registered + allow-listed target {target.name!r} "
            f"id={target.id} connector={target.connector_type}"
        )


async def cmd_allowlist_target(args: argparse.Namespace) -> None:
    from app.models import Target

    async with get_session_factory()() as session:
        target = await session.get(Target, args.id)
        if target is None:
            raise SystemExit(f"target {args.id} not found")
        target.allowlisted = args.allow
        target.approved_by = args.approved_by if args.allow else None
        target.approval_note = args.note or ""
        await session.commit()
        state = "allow-listed" if args.allow else "de-listed"
        print(f"Target {target.name!r} {state}")


async def cmd_list_targets(args: argparse.Namespace) -> None:
    from sqlalchemy import select

    from app.models import Target

    async with get_session_factory()() as session:
        rows = (await session.execute(select(Target).order_by(Target.created_at))).scalars().all()
        for t in rows:
            print(
                f"{t.id}  {t.name:<24} {t.connector_type:<10} "
                f"{'ALLOW-LISTED' if t.allowlisted else 'blocked':<12} {t.endpoint}"
            )


async def cmd_list_packs(args: argparse.Namespace) -> None:
    from sqlalchemy import func, select

    from app.models import Payload, PayloadPack

    async with get_session_factory()() as session:
        counts: dict[str, int] = dict(
            (
                await session.execute(
                    select(Payload.pack_id, func.count(Payload.id)).group_by(Payload.pack_id)
                )
            ).all()
        )
        packs = (await session.execute(select(PayloadPack).order_by(PayloadPack.name))).scalars().all()
        for p in packs:
            print(
                f"{p.name:<20} v{p.version:<8} {counts.get(p.id, 0):>3} payloads  "
                f"OWASP {','.join(p.owasp_categories or [])}"
            )


async def cmd_run(args: argparse.Namespace) -> None:
    from app.agents.orchestrator import AttackOrchestrator, materialize_payloads
    from app.models import Run, Target

    async with get_session_factory()() as session:
        user = await _admin_user(session)
        target = await session.get(Target, args.target)
        if target is None:
            raise SystemExit(f"target {args.target} not found")
        if not target.allowlisted:
            raise SystemExit(
                f"target {target.name!r} is NOT allow-listed — refusing to run. "
                "Use `allowlist-target` first."
            )
        pack_ids = await _resolve_packs(
            session, [p.strip() for p in args.packs.split(",") if p.strip()]
        )
        dry_run = args.dry_run if args.dry_run is not None else get_settings().dry_run_default
        run = Run(
            target_id=target.id,
            payload_pack_ids=pack_ids,
            status="scheduled",
            dry_run=dry_run,
            started_by=user.id,
            max_turns=args.max_turns or get_settings().default_max_turns,
            token_budget=target.max_tokens_per_run or get_settings().default_max_tokens_per_run,
        )
        session.add(run)
        await session.flush()
        run_id = run.id
        payloads = await materialize_payloads(session, pack_ids)
        orchestrator = AttackOrchestrator(session, run, target, payloads)
        mode = "DRY-RUN" if dry_run else "LIVE"
        print(f"[{mode}] launching run {run_id} against {target.name} "
              f"({len(payloads)} payloads, {run.max_turns} max turns)")
        await orchestrator.execute()
        await session.commit()
        await _print_run_summary(session, run_id)


async def _print_run_summary(session, run_id: str) -> None:
    from sqlalchemy import select

    from app.models import AgentEvent, Finding, Run

    run = await session.get(Run, run_id)
    events = (
        await session.execute(
            select(AgentEvent).where(AgentEvent.run_id == run_id).order_by(AgentEvent.sequence)
        )
    ).scalars().all()
    findings = (
        await session.execute(select(Finding).where(Finding.run_id == run_id))
    ).scalars().all()
    print(f"\nRun {run_id} -> {run.status} ({run.tokens_used} tokens, "
          f"${run.cost_estimate_usd:.4f})")
    for e in events:
        print(f"  [{e.sequence:>2}] {e.agent:<12} {e.event_type:<24} {_event_summary(e)}")
    print(f"\nFindings: {len(findings)}")
    for f in findings:
        print(
            f"  {f.severity.upper():<8} {f.confidence:.0%}  {f.category:<22} "
            f"OWASP {f.owasp_category} ATLAS {f.mitre_atlas_id}\n"
            f"           {f.title}"
        )


def _event_summary(e: Any) -> str:
    p = e.payload or {}
    if e.event_type == "payload_selected":
        return f"{p.get('slug', '')} (risk={p.get('risk')})"
    if e.event_type == "target_response":
        return f"status={p.get('status_code')} tokens={p.get('tokens')}"
    if e.event_type == "verdict":
        return f"success={p.get('success')} severity={p.get('severity')} conf={p.get('confidence')}"
    if e.event_type == "mutation":
        return f"strategy={p.get('strategy')}"
    if e.event_type == "finding_recorded":
        return f"{p.get('category')} [{p.get('severity')}]"
    if e.event_type == "run_finished":
        return f"status={p.get('status')} findings={p.get('findings')}"
    if e.event_type in {"safety_blocked", "run_failed"}:
        return str(p.get('message') or p.get('error'))
    return ""


async def cmd_findings(args: argparse.Namespace) -> None:
    from sqlalchemy import select

    from app.models import Finding

    async with get_session_factory()() as session:
        stmt = select(Finding).order_by(Finding.created_at.desc())
        if args.run:
            stmt = stmt.where(Finding.run_id == args.run)
        if args.severity:
            stmt = stmt.where(Finding.severity == args.severity.lower())
        if args.category:
            stmt = stmt.where(Finding.category == args.category)
        rows = (await session.execute(stmt)).scalars().all()
        for f in rows:
            print(
                f"{f.id}  {f.severity.upper():<8} {f.confidence:.0%}  {f.category:<22} "
                f"{f.title}  (run {f.run_id[:8]})"
            )


async def cmd_report(args: argparse.Namespace) -> None:
    from app.reporting.report_service import generate_report

    async with get_session_factory()() as session:
        report = await generate_report(session, args.run, args.format, generated_by="cli")
        await session.commit()
        print(f"{args.format.upper()} report -> {report.storage_path} "
              f"({report.size_bytes} bytes)")


# ── demo ────────────────────────────────────────────────────────────────────
async def cmd_demo(args: argparse.Namespace) -> None:
    """End-to-end demo: mock target + dry-run + live run + reports."""
    import threading

    import uvicorn

    from mock_target.main import app as mock_app

    port = get_settings().mock_target_port
    server = uvicorn.Server(uvicorn.Config(mock_app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    import httpx

    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            async with httpx.AsyncClient() as client:
                if (await client.get(f"{base}/healthz")).status_code == 200:
                    break
        except Exception:
            await asyncio.sleep(0.2)
    else:
        raise SystemExit("mock target did not start")

    print("=" * 72)
    print("Aegis-LLM demo: vulnerable mock target (Acme Chat) + attack run")
    print("=" * 72)

    await init_db()
    from app.services.bootstrap import bootstrap

    async with get_session_factory()() as session:
        await bootstrap(session)
        user = await _admin_user(session)
        from app.models import Target

        target = Target(
            name="acme-chat-demo",
            description="Bundled deliberately vulnerable mock target",
            connector_type="rest",
            endpoint=f"{base}/chat",
            config={"response_path": "reply"},
            owner_id=user.id,
            allowlisted=True,
            approved_by=user.username,
            approval_note="Demo target; explicitly authorized for testing.",
        )
        session.add(target)
        await session.flush()
        target_id = target.id

        from app.agents.orchestrator import AttackOrchestrator, materialize_payloads
        from app.models import Run

        pack_ids = await _resolve_packs(
            session, ["prompt-injection", "jailbreak", "data-exfiltration", "tool-abuse"]
        )

        # 1) Dry run first — validates the pipeline, touches nothing.
        dry = Run(
            target_id=target_id, payload_pack_ids=pack_ids, status="scheduled",
            dry_run=True, started_by=user.id,
            max_turns=get_settings().default_max_turns,
            token_budget=get_settings().default_max_tokens_per_run,
        )
        session.add(dry)
        await session.flush()
        print("\n[1/3] DRY-RUN (no requests touch the real target) ...")
        await AttackOrchestrator(session, dry, target, await materialize_payloads(session, pack_ids)).execute()
        await session.commit()
        print(f"      dry-run finished: status={dry.status} — no findings expected")

        # 2) Live run with streaming events.
        live = Run(
            target_id=target_id, payload_pack_ids=pack_ids, status="scheduled",
            dry_run=False, started_by=user.id,
            max_turns=get_settings().default_max_turns,
            token_budget=get_settings().default_max_tokens_per_run,
        )
        session.add(live)
        await session.flush()
        run_id = live.id
        print("\n[2/3] LIVE run (authorized demo target) ...")
        await AttackOrchestrator(session, live, target, await materialize_payloads(session, pack_ids)).execute()
        await session.commit()
        await _print_run_summary(session, run_id)

        # 3) Reports.
        from app.reporting.report_service import generate_report

        print("\n[3/3] Generating reports ...")
        for fmt in ("html", "sarif", "json"):
            report = await generate_report(session, run_id, fmt, generated_by="cli")
            await session.commit()
            print(f"      {fmt.upper():<4} -> {report.storage_path}")

        print("\nDone. Explore via the REST API (`uvicorn app.main:app`) or the CLI.")


# ── entrypoint ──────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aegis", description="Aegis-LLM CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init-db", help="create tables + seed roles/admin/packs")
    p.set_defaults(func=cmd_init_db)

    p = sub.add_parser("register-target", help="register + allow-list a target")
    p.add_argument("--name", required=True)
    p.add_argument("--connector-type", required=True, choices=["rest", "browser", "websocket"])
    p.add_argument("--endpoint", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--config", default="", help='JSON, e.g. \'{"response_path": "reply"}\'')
    p.add_argument("--approved-by", default="")
    p.add_argument("--approval-note", default="")
    p.set_defaults(func=cmd_register_target)

    p = sub.add_parser("allowlist-target", help="allow-list / de-list a target")
    p.add_argument("--id", required=True)
    p.add_argument("--allow", action="store_true", default=True)
    p.add_argument("--no-allow", dest="allow", action="store_false")
    p.add_argument("--approved-by", default="")
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_allowlist_target)

    p = sub.add_parser("list-targets")
    p.set_defaults(func=cmd_list_targets)

    p = sub.add_parser("list-packs")
    p.set_defaults(func=cmd_list_packs)

    p = sub.add_parser("run", help="launch an attack run")
    p.add_argument("--target", required=True)
    p.add_argument("--packs", required=True, help="comma-separated pack names")
    p.add_argument("--dry-run", action="store_true", default=None)
    p.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    p.add_argument("--max-turns", type=int, default=None)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("findings")
    p.add_argument("--run", default=None)
    p.add_argument("--severity", default=None)
    p.add_argument("--category", default=None)
    p.set_defaults(func=cmd_findings)

    p = sub.add_parser("report")
    p.add_argument("--run", required=True)
    p.add_argument("--format", default="html", choices=["html", "sarif", "json"])
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("demo", help="end-to-end demo against the bundled mock target")
    p.set_defaults(func=cmd_demo)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    asyncio.run(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
