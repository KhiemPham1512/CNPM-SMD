"""
File Mutation Authorization Policy

Determines if a user can perform mutations (upload/replace/rename/delete) on files.
Rules:
- Only LECTURER role
- Must be owner of the syllabus/version
- Version status must be DRAFT
"""
import logging
from typing import List, Optional
from domain.constants import ROLE_LECTURER, WORKFLOW_DRAFT

logger = logging.getLogger(__name__)


def can_edit_file(
    user_id: int,
    user_roles: List[str],
    version_workflow_status: str,
    version_created_by: int
) -> bool:
    """
    Check if user can edit (upload/replace/rename/delete) files for a syllabus version.
    
    Rules:
    1. User must have LECTURER role
    2. User must be the owner (version.created_by == user_id)
    3. Version status must be DRAFT
    
    Args:
        user_id: Current user ID
        user_roles: List of user roles
        version_workflow_status: Workflow status of the syllabus version
        version_created_by: User ID who created the version
        
    Returns:
        True if user can edit files, False otherwise
    """
    if not user_roles:
        return False
    
    # Must be LECTURER
    if ROLE_LECTURER not in user_roles:
        return False
    
    # Must be owner
    if version_created_by != user_id:
        return False
    
    # Must be DRAFT status
    if version_workflow_status != WORKFLOW_DRAFT:
        return False
    
    return True
