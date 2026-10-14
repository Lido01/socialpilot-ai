"""Platform Owner admin endpoints for company registration management."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import get_db, get_platform_owner
from app.core.exceptions import ConflictError, ResourceNotFoundError, ValidationError
from app.models import (
    AuditLog,
    Company,
    CompanyMembership,
    CompanyRegistrationRequest,
    CompanyStatus,
    MembershipRole,
    User,
)
from app.schemas.platform import (
    ApproveCompanyRequest,
    PendingCompanyResponse,
    PlatformActionResponse,
    RejectCompanyRequest,
)

router = APIRouter(prefix="/owner-admin", tags=["platform-owner"])


def _get_client_ip(request: Request) -> str | None:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get(
    "/companies/pending",
    response_model=list[PendingCompanyResponse],
)
def list_pending_companies(
    _platform_owner: User = Depends(get_platform_owner),
    db: Session = Depends(get_db),
) -> list[PendingCompanyResponse]:
    """List all pending company registration requests.

    Only accessible by the Platform Owner.
    """
    requests = (
        db.query(CompanyRegistrationRequest)
        .join(User, CompanyRegistrationRequest.user_id == User.id)
        .filter(CompanyRegistrationRequest.status == CompanyStatus.PENDING)
        .order_by(CompanyRegistrationRequest.created_at.asc())
        .all()
    )

    result = []
    for req in requests:
        result.append(
            PendingCompanyResponse(
                id=req.id,
                name=req.name,
                normalized_name=req.normalized_name,
                industry=req.industry,
                website=req.website,
                country=req.country,
                contact_email=req.contact_email,
                status=req.status,
                user_id=req.user.id,
                user_telegram_id=req.user.telegram_id,
                user_display_name=req.user.display_name,
                user_username=req.user.username,
                created_at=req.created_at.isoformat(),
                updated_at=req.updated_at.isoformat(),
            )
        )
    return result


@router.post(
    "/companies/{request_id}/approve",
    response_model=PlatformActionResponse,
    status_code=status.HTTP_200_OK,
)
def approve_company(
    request_id: str,
    request: Request,
    _request: ApproveCompanyRequest,
    platform_owner: User = Depends(get_platform_owner),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> PlatformActionResponse:
    """Approve a pending company registration.

    Creates the company with 'active' status and establishes the initial
    Company Admin membership for the requesting user.
    """
    reg_request = (
        db.query(CompanyRegistrationRequest)
        .filter(
            CompanyRegistrationRequest.id == request_id,
            CompanyRegistrationRequest.status == CompanyStatus.PENDING,
        )
        .first()
    )

    if not reg_request:
        raise ResourceNotFoundError("Pending registration request not found")

    existing_company = (
        db.query(Company)
        .filter(
            Company.normalized_name == reg_request.normalized_name,
            Company.owner_user_id == reg_request.user_id,
            Company.status.in_([CompanyStatus.ACTIVE, CompanyStatus.PENDING]),
        )
        .first()
    )
    if existing_company:
        raise ConflictError(
            "Company with this name already exists for this user",
            details=[{"field": "normalized_name", "code": "DUPLICATE_COMPANY"}],
        )

    company = Company(
        name=reg_request.name,
        normalized_name=reg_request.normalized_name,
        industry=reg_request.industry,
        website=reg_request.website,
        country=reg_request.country,
        contact_email=reg_request.contact_email,
        status=CompanyStatus.ACTIVE,
        owner_user_id=reg_request.user_id,
    )
    db.add(company)
    db.flush()

    membership = CompanyMembership(
        company_id=company.id,
        user_id=reg_request.user_id,
        role=MembershipRole.COMPANY_ADMIN,
        is_active=True,
    )
    db.add(membership)

    reg_request.status = CompanyStatus.APPROVED
    reg_request.company_id = company.id
    reg_request.reviewed_by = platform_owner.id
    reg_request.reviewed_at = datetime.now(timezone.utc)

    audit = AuditLog(
        company_id=company.id,
        actor_user_id=platform_owner.id,
        action="company.approved",
        entity_type="company",
        entity_id=company.id,
        meta={"registration_request_id": request_id, "previous_status": CompanyStatus.PENDING},
        ip_address=_get_client_ip(request),
    )
    db.add(audit)

    db.commit()

    return PlatformActionResponse(
        success=True,
        message="Company approved and activated",
        company_id=company.id,
        company_status=CompanyStatus.ACTIVE,
    )


@router.post(
    "/companies/{request_id}/reject",
    response_model=PlatformActionResponse,
    status_code=status.HTTP_200_OK,
)
def reject_company(
    request_id: str,
    request: Request,
    _request: RejectCompanyRequest,
    platform_owner: User = Depends(get_platform_owner),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> PlatformActionResponse:
    """Reject a pending company registration.

    Sets the registration request status to 'rejected' with a reason.
    """
    reg_request = (
        db.query(CompanyRegistrationRequest)
        .filter(
            CompanyRegistrationRequest.id == request_id,
            CompanyRegistrationRequest.status == CompanyStatus.PENDING,
        )
        .first()
    )

    if not reg_request:
        raise ResourceNotFoundError("Pending registration request not found")

    reg_request.status = CompanyStatus.REJECTED
    reg_request.rejection_reason = _request.reason.strip()
    reg_request.reviewed_by = platform_owner.id
    reg_request.reviewed_at = datetime.now(timezone.utc)

    audit = AuditLog(
        company_id=None,
        actor_user_id=platform_owner.id,
        action="company.rejected",
        entity_type="company_registration_request",
        entity_id=reg_request.id,
        meta={"reason": _request.reason.strip()},
        ip_address=_get_client_ip(request),
    )
    db.add(audit)

    db.commit()

    return PlatformActionResponse(
        success=True,
        message="Company registration rejected",
        company_id=None,
        company_status=CompanyStatus.REJECTED,
    )


@router.post(
    "/companies/{request_id}/request-info",
    response_model=PlatformActionResponse,
    status_code=status.HTTP_200_OK,
)
def request_more_info(
    request_id: str,
    request: Request,
    _request: RejectCompanyRequest,
    platform_owner: User = Depends(get_platform_owner),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> PlatformActionResponse:
    """Request more information for a pending company registration.

    Sets the registration request status to 'info_requested' with a reason.
    """
    reg_request = (
        db.query(CompanyRegistrationRequest)
        .filter(
            CompanyRegistrationRequest.id == request_id,
            CompanyRegistrationRequest.status == CompanyStatus.PENDING,
        )
        .first()
    )

    if not reg_request:
        raise ResourceNotFoundError("Pending registration request not found")

    reg_request.status = CompanyStatus.INFO_REQUESTED
    reg_request.rejection_reason = _request.reason.strip()
    reg_request.reviewed_by = platform_owner.id
    reg_request.reviewed_at = datetime.now(timezone.utc)

    audit = AuditLog(
        company_id=None,
        actor_user_id=platform_owner.id,
        action="company.info_requested",
        entity_type="company_registration_request",
        entity_id=reg_request.id,
        meta={"reason": _request.reason.strip()},
        ip_address=_get_client_ip(request),
    )
    db.add(audit)

    db.commit()

    return PlatformActionResponse(
        success=True,
        message="More information requested",
        company_id=None,
        company_status=CompanyStatus.INFO_REQUESTED,
    )