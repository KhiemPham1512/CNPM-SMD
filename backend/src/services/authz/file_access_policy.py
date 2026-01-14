"""
File Access Policy

Authorization policy for file view/download based on role and workflow status.
Implements rules as specified in SMD project documentation.
"""
import logging
from typing import List, Optional

from domain.constants import (
    ROLE_ADMIN, ROLE_LECTURER, ROLE_HOD, ROLE_AA, ROLE_PRINCIPAL, ROLE_STUDENT,
    WORKFLOW_DRAFT, WORKFLOW_PENDING_REVIEW, WORKFLOW_PENDING_APPROVAL,
    WORKFLOW_APPROVED, WORKFLOW_PUBLISHED
)

logger = logging.getLogger(__name__)


def can_view_file(
    user_id: int,
    user_roles: List[str],
    version_workflow_status: str,
    version_created_by: int
) -> bool:
    """
    Check if user can view/download a file based on role and workflow status.
    
    Rules (as per SMD documentation):
    - LECTURER: Can view files of syllabus they created (any status) OR files of PUBLISHED syllabus
    - HOD: Can view files when syllabus status >= PENDING_REVIEW
    - AA: Can view files when syllabus status >= PENDING_APPROVAL
    - PRINCIPAL: Can view files when syllabus status >= APPROVED
    - STUDENT/PUBLIC: Can only view files when syllabus status == PUBLISHED
    - ADMIN: Can view all files (system administration)
    
    Args:
        user_id: User ID requesting access
        user_roles: List of user roles (e.g., ['LECTURER', 'HOD'])
        version_workflow_status: Workflow status of the syllabus version (DRAFT, PENDING_REVIEW, etc.)
        version_created_by: User ID who created the syllabus version
        
    Returns:
        True if user can view file, False otherwise
    """
    if not user_roles:
        logger.warning(f"can_view_file called with empty user_roles for user_id={user_id}")
        return False
    
    # ADMIN: Can view all files
    if ROLE_ADMIN in user_roles:
        return True
    
    # LECTURER: Can view files they created (any status) OR files of PUBLISHED syllabus
    if ROLE_LECTURER in user_roles:
        if version_created_by == user_id:
            # Owner can view their own files regardless of status
            return True
        if version_workflow_status == WORKFLOW_PUBLISHED:
            # Can view any published syllabus files
            return True
        return False
    
    # HOD: Can view when status >= PENDING_REVIEW
    if ROLE_HOD in user_roles:
        return _is_status_gte(version_workflow_status, WORKFLOW_PENDING_REVIEW)
    
    # AA: Can view when status >= PENDING_APPROVAL
    if ROLE_AA in user_roles:
        return _is_status_gte(version_workflow_status, WORKFLOW_PENDING_APPROVAL)
    
    # PRINCIPAL: Can view when status >= APPROVED
    if ROLE_PRINCIPAL in user_roles:
        return _is_status_gte(version_workflow_status, WORKFLOW_APPROVED)
    
    # STUDENT/PUBLIC: Can only view when status == PUBLISHED
    if ROLE_STUDENT in user_roles:
        return version_workflow_status == WORKFLOW_PUBLISHED
    
    # Unknown role - deny access
    logger.warning(f"Unknown role in user_roles={user_roles} for user_id={user_id}")
    return False


def _is_status_gte(status: str, min_status: str) -> bool:
    """
    Check if workflow status is greater than or equal to minimum status.
    
    Workflow order: DRAFT < PENDING_REVIEW < PENDING_APPROVAL < APPROVED < PUBLISHED
    
    Args:
        status: Current workflow status
        min_status: Minimum required status
        
    Returns:
        True if status >= min_status
    """
    status_order = {
        WORKFLOW_DRAFT: 0,
        WORKFLOW_PENDING_REVIEW: 1,
        WORKFLOW_PENDING_APPROVAL: 2,
        WORKFLOW_APPROVED: 3,
        WORKFLOW_PUBLISHED: 4,
    }
    
    current_level = status_order.get(status, -1)
    min_level = status_order.get(min_status, -1)
    
    if current_level == -1 or min_level == -1:
        logger.warning(f"Unknown status: status={status}, min_status={min_status}")
        return False
    
    return current_level >= min_level
