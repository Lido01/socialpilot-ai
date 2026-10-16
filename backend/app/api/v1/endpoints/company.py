"""Company registration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user, get_db
from app.core.exceptions import ConflictError, ValidationError
from app.models import (
    Company,
    CompanyRegistrationRequest,
    CompanyStatus,
    RegistrationStatus,
    User,
)
from app.schemas.company import (
    CompanyRegistrationRequestCreate,
    CompanyRegistrationRequestResponse,
    CompanyResponse,
)

router = APIRouter(prefix="/companies", tags=["companies"])


def _normalize_name(name: str) -> str:
    """Normalize company name for duplicate detection."""
    return name.strip().lower()


@router.post(
    "/register",
    response_model=CompanyRegistrationRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_company(
    request: CompanyRegistrationRequestCreate,
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> CompanyRegistrationRequestResponse:
    """Submit a company registration request.

    Creates a pending registration request. The company is created with
    status 'pending' and the user becomes the Company Admin upon approval.

    Business rules:
    - User cannot have duplicate pending requests for the same normalized name
    - User cannot register another company with the same normalized name as an existing active company
    """
    normalized = _normalize_name(request.name)

    existing_pending = (
        db.query(CompanyRegistrationRequest)
        .filter(
            CompanyRegistrationRequest.user_id == current_user.id,
            CompanyRegistrationRequest.normalized_name == normalized,
            CompanyRegistrationRequest.status == RegistrationStatus.PENDING,
        )
        .first()
    )
    if existing_pending:
        raise ConflictError(
            "A pending registration request with this name already exists",
            details=[{"field": "name", "code": "DUPLICATE_PENDING"}],
        )

    existing_active = (
        db.query(Company)
        .filter(
            Company.owner_user_id == current_user.id,
            Company.normalized_name == normalized,
            Company.status.in_(["active", "pending"]),
        )
        .first()
    )
    if existing_active:
        raise ConflictError(
            "You already own a company with this name",
            details=[{"field": "name", "code": "DUPLICATE_COMPANY"}],
        )

    reg_request = CompanyRegistrationRequest(
        user_id=current_user.id,
        name=request.name.strip(),
        normalized_name=normalized,
        industry=request.industry,
        website=request.website,
        country=request.country,
        contact_email=request.contact_email,
        status=RegistrationStatus.PENDING,
    )

    db.add(reg_request)

    try:
        db.commit()
        db.refresh(reg_request)
    except sa_exc.IntegrityError as e:
        db.rollback()
        raise ConflictError("Registration conflict") from e

    return CompanyRegistrationRequestResponse.model_validate(reg_request)


@router.get(
    "/registrations/me",
    response_model=list[CompanyRegistrationRequestResponse],
)
def list_my_registrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CompanyRegistrationRequestResponse]:
    """List the current user's registration requests."""
    requests = (
        db.query(CompanyRegistrationRequest)
        .filter(CompanyRegistrationRequest.user_id == current_user.id)
        .order_by(CompanyRegistrationRequest.created_at.desc())
        .all()
    )
    return [CompanyRegistrationRequestResponse.model_validate(r) for r in requests]


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
)
def get_company(
    company_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompanyResponse:
    """Get company details (requires membership)."""
    from app.core.deps import require_company_membership

    membership = require_company_membership(company_id, current_user, db)
    company = membership.company
    return CompanyResponse.model_validate(company)