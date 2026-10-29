from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserSchema(BaseSchema):
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DogTrainingSessionSchema(BaseSchema):
    id: str
    user_id: str
    session_date: datetime
    title: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DogCommandMasterySchema(BaseSchema):
    id: str
    session_id: str
    command_name: str
    mastered: bool = False
    confidence: Optional[int] = None
    notes: Optional[str] = None
    mastered_at: Optional[datetime] = None
    created_at: datetime


class ShoeSchema(BaseSchema):
    id: str
    user_id: str
    name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    mileage_km: Optional[float] = None
    retired: bool = False
    created_at: datetime
    updated_at: datetime


class RunningWorkoutSchema(BaseSchema):
    id: str
    user_id: str
    shoe_id: Optional[str] = None
    session_date: datetime
    distance_km: float
    duration_minutes: int
    pace_per_km: Optional[float] = None
    avg_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    calories: Optional[int] = None
    terrain: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BeltRankSchema(BaseSchema):
    id: str
    user_id: str
    rank_name: str
    awarded_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class KarateTrainingSessionSchema(BaseSchema):
    id: str
    user_id: str
    belt_id: Optional[str] = None
    session_date: datetime
    kata_name: Optional[str] = None
    focus_area: Optional[str] = None
    duration_minutes: int
    training_hours: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ClientSchema(BaseSchema):
    id: str
    user_id: str
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectSchema(BaseSchema):
    id: str
    user_id: str
    client_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    status: str = "PLANNING"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget_amount: Optional[float] = None
    hourly_rate: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class TimeEntrySchema(BaseSchema):
    id: str
    user_id: str
    project_id: Optional[str] = None
    entry_date: datetime
    hours: float
    description: Optional[str] = None
    billable: bool = True
    client_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class InvoiceSchema(BaseSchema):
    id: str
    user_id: str
    project_id: Optional[str] = None
    invoice_number: str
    issued_date: datetime
    due_date: Optional[datetime] = None
    total_amount: float
    status: str = "DRAFT"
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ExpenseSchema(BaseSchema):
    id: str
    user_id: str
    expense_date: datetime
    category: str
    description: str
    amount: float
    tax_amount: Optional[float] = None
    vendor: Optional[str] = None
    notes: Optional[str] = None
    receipt_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReceiptSchema(BaseSchema):
    id: str
    file_name: str
    storage_path: str
    mime_type: Optional[str] = None
    hash: Optional[str] = None
    uploaded_at: datetime


class ContactSchema(BaseSchema):
    id: str
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    relationship_type: str = "OTHER"
    birthday: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SpecialDateSchema(BaseSchema):
    id: str
    user_id: str
    contact_id: Optional[str] = None
    title: str
    date: datetime
    reminder_days: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class JournalEntrySchema(BaseSchema):
    id: str
    user_id: str
    project_id: Optional[str] = None
    title: str
    content: str
    status: str = "DRAFT"
    category: str = "OTHER"
    reported_at: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    activity_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AIPlanSchema(BaseSchema):
    id: str
    user_id: str
    title: str
    prompt: str
    summary: Optional[str] = None
    status: str = "draft"
    scheduled_for: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AIReminderSchema(BaseSchema):
    id: str
    user_id: str
    message: str
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    acked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
