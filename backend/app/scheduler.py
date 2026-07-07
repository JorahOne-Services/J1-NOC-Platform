"""Background collector loop (dependency-free; uses asyncio).

Starts on app startup via the FastAPI lifespan and runs every collector on a
fixed interval. ``run_all`` is CPU-bound/sync (httpx, ldap, snmp) so we run it in
a worker thread to avoid blocking the event loop. The loop never raises.
"""
from __future__ import annotations

import asyncio
import logging

from .collectors import run_all

logger = logging.getLogger("jnop.scheduler")
INTERVAL_SECONDS = 60


async def collector_loop() -> None:
    logger.info("collector loop starting (interval=%ss)", INTERVAL_SECONDS)
    # Run once immediately so dashboards populate without waiting a full interval.
    try:
        await asyncio.to_thread(run_all)
    except Exception:
        logger.exception("collector loop initial run failed")
    while True:
        try:
            await asyncio.sleep(INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("collector loop cancelled")
            break
        try:
            await asyncio.to_thread(run_all)
        except Exception:  # defensive backstop
            logger.exception("collector loop iteration failed")
