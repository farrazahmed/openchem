"""
Audit trail: logs every create/update/delete action with before/after snapshots.
"""

import json
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models import AuditLog


def _serialize(obj) -> str | None:
    """Convert a SQLAlchemy model instance to a JSON string for audit logging."""
    if obj is None:
        return None
    data = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, (date, datetime)):
            val = val.isoformat()
        data[col.name] = val
    return json.dumps(data)


def log_action(
    db: Session,
    *,
    user: str,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    deal_ref: str | None = None,
    details: str | None = None,
    before: object | None = None,
    after: object | None = None,
):
    entry = AuditLog(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        deal_ref=deal_ref,
        details=details,
        before_state=_serialize(before),
        after_state=_serialize(after),
    )
    db.add(entry)
