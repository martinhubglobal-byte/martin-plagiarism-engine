
"""Secure per-Firebase-user tenant resolution."""

from __future__ import annotations

import hmac
import os
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from noplag_engine.db import get_sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield a fresh database session per request."""
    async with get_sessionmaker()() as session:
        yield session


async def get_tenant_id(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> UUID:
    """Resolve the private tenant belonging to a verified Firebase user."""

    expected_secret = os.environ.get("WORKER_SHARED_SECRET")
    supplied_secret = request.headers.get("X-Worker-Secret", "")
    firebase_uid = request.headers.get(
        "X-Verified-Firebase-UID", ""
    ).strip()

    if not expected_secret:
        raise HTTPException(
            status_code=503,
            detail="Worker authentication is not configured.",
        )

    if not hmac.compare_digest(supplied_secret, expected_secret):
        raise HTTPException(
            status_code=401,
            detail="Trusted worker authentication failed.",
        )

    if not firebase_uid or len(firebase_uid) > 128:
        raise HTTPException(
            status_code=401,
            detail="Verified Firebase identity is missing.",
        )

    async with session.begin():
        # Serialize first-time tenant creation for the same Firebase UID.
        await session.execute(
            text(
                "SELECT pg_advisory_xact_lock("
                "hashtextextended(:firebase_uid, 0))"
            ),
            {"firebase_uid": firebase_uid},
        )

        result = await session.execute(
            text(
                """
                SELECT tenant_id
                FROM firebase_user_tenants
                WHERE firebase_uid = :firebase_uid
                """
            ),
            {"firebase_uid": firebase_uid},
        )

        tenant_id = result.scalar_one_or_none()

        if tenant_id is None:
            tenant_result = await session.execute(
                text(
                    """
                    INSERT INTO tenants (name)
                    VALUES ('Martin Global Academy student')
                    RETURNING id
                    """
                )
            )

            tenant_id = tenant_result.scalar_one()

            await session.execute(
                text(
                    """
                    INSERT INTO firebase_user_tenants
                        (firebase_uid, tenant_id)
                    VALUES (:firebase_uid, :tenant_id)
                    """
                ),
                {
                    "firebase_uid": firebase_uid,
                    "tenant_id": tenant_id,
                },
            )

    return UUID(str(tenant_id))
