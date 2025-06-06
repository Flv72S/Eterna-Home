from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime

class MaintenanceExportParams(BaseModel):
    format: str = "csv"
    status: Optional[str] = None
    record_type: Optional[str] = None
    node_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        if v not in ["csv", "json"]:
            raise ValueError("Format must be either 'csv' or 'json'")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        if v and info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v 