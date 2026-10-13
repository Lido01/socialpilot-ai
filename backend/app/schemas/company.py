"""Company registration schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompanyRegistrationRequestCreate(BaseModel):
    """Request to submit a company registration."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Company display name",
    )
    industry: str | None = Field(
        default=None,
        max_length=128,
        description="Company industry",
    )
    website: str | None = Field(
        default=None,
        max_length=512,
        description="Company website URL",
    )
    country: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}$",
        description="ISO 3166-1 alpha-2 country code",
    )
    contact_email: str | None = Field(
        default=None,
        max_length=255,
        description="Contact email",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Company name cannot be empty or whitespace")
        return stripped

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if stripped and not (stripped.startswith("http://") or stripped.startswith("https://")):
                raise ValueError("Website must start with http:// or https://")
            return stripped or None
        return v

    @field_validator("contact_email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if stripped and "@" not in stripped:
                raise ValueError("Invalid email format")
            return stripped or None
        return v


class CompanyRegistrationRequestResponse(BaseModel):
    """Response for company registration request."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    normalized_name: str
    industry: str | None
    website: str | None
    country: str | None
    contact_email: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class CompanyResponse(BaseModel):
    """Response for company data."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    normalized_name: str
    industry: str | None
    website: str | None
    country: str | None
    contact_email: str | None
    status: str
    created_at: datetime
    updated_at: datetime