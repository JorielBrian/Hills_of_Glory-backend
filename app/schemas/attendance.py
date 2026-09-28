import uuid
from datetime import datetime

from pydantic import BaseModel


class AttendanceScanRequest(BaseModel):
    """The door scanner reads a person's QR code and posts it along with the event instance."""

    qr_code: str
    event_instance_id: uuid.UUID


class AttendanceRecordOut(BaseModel):
    id: uuid.UUID
    event_instance_id: uuid.UUID
    person_id: uuid.UUID
    scanned_by_id: uuid.UUID | None
    scanned_at: datetime

    model_config = {"from_attributes": True}
