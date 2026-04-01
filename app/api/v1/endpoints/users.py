"""
User endpoints.

According to IPChain MVP specification:
- GET /api/users/me/profile
- PUT /api/users/me/profile
- GET /api/users/me/roles
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import (
    ProfileRead,
    ProfileUpdate,
    UserWithProfileRead,
    RoleStatusResponse,
)
from app.repositories.user_repository import UserRepository

router = APIRouter()


@router.get(
    "/me/profile",
    response_model=UserWithProfileRead,
    summary="Get current user profile",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Read current user profile with extended identity information.
    
    Returns user data with embedded profile containing
    legal_name, country, and other PII fields.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_with_profile(current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    
    return user


@router.put(
    "/me/profile",
    response_model=UserWithProfileRead,
    summary="Update current user profile",
)
async def update_current_user_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update minimal profile fields.
    
    Updates legal_name, dob, country, address.
    PII fields are stored securely and accessed only by authorized users.
    """
    user_repo = UserRepository(db)
    
    # Get or create profile
    profile = await user_repo.get_profile(current_user.id)
    
    if not profile:
        # Create profile if doesn't exist
        from app.models.user import Profile
        profile = Profile(
            user_id=current_user.id,
            legal_name=data.legal_name,
            dob=data.dob,
            country=data.country,
            address=data.address,
        )
        profile = await user_repo.create_profile(profile)
    else:
        # Update existing profile
        profile = await user_repo.update_profile(
            profile,
            legal_name=data.legal_name,
            dob=data.dob,
            country=data.country,
            address=data.address,
        )
    
    # Reload user with profile
    user = await user_repo.get_with_profile(current_user.id)
    return user


@router.get(
    "/me/roles",
    response_model=RoleStatusResponse,
    summary="Get user role and status",
)
async def get_user_roles(
    current_user: User = Depends(get_current_user),
):
    """
    Return role and status snapshot.
    
    Returns minimal user data with role and status
    for authorization decisions.
    """
    return RoleStatusResponse(
        user_id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        status=current_user.status,
        wallet_address=current_user.wallet_address,
    )
