import logging
from typing import Tuple

from flask import Blueprint, Response, jsonify, request
from sqlalchemy.exc import IntegrityError

from api.schemas.syllabus import SyllabusCreateSchema, SyllabusResponseSchema, SyllabusUpdateSchema
from api.responses import success_response, error_response, not_found_response, validation_error_response
from api.utils.authz import get_user_id_from_token, get_user_roles, role_required, token_required
from api.utils.db import get_db_session
from dependency_container import container
from domain.exceptions import ValidationException, UnauthorizedException
from domain.constants import ROLE_STUDENT

logger = logging.getLogger(__name__)

# Import standardized role constants from SyllabusService
ROLE_LECTURER = 'LECTURER'
ROLE_HOD = 'HOD'
ROLE_AA = 'AA'
ROLE_ADMIN = 'ADMIN'
ROLE_PRINCIPAL = 'PRINCIPAL'

bp = Blueprint('syllabus', __name__, url_prefix='/syllabi')

create_schema = SyllabusCreateSchema()
update_schema = SyllabusUpdateSchema()
response_schema = SyllabusResponseSchema()


@bp.route('/', methods=['GET'])
@token_required
def list_syllabi() -> Tuple[Response, int]:
    """
    Get all syllabi or filter by owner
    ---
    get:
      summary: Get all syllabi or filter by owner (mine=true)
      security:
        - Bearer: []
      tags:
        - Syllabi
      parameters:
        - name: mine
          in: query
          required: false
          schema:
            type: boolean
          description: If true, return only syllabi owned by current user
      responses:
        200:
          description: List of syllabi
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabi retrieved successfully"
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        
        # Check if mine=true filter is requested
        mine = request.args.get('mine', 'false').lower() == 'true'
        if mine:
            user_id = get_user_id_from_token()
            if not user_id:
                return error_response('User not authenticated', 401)
            syllabi = syllabus_service.list_syllabi_by_owner(user_id)
        else:
            syllabi = syllabus_service.list_syllabi()
        
        syllabi_data = response_schema.dump(syllabi, many=True)
        return success_response(data=syllabi_data, message='Syllabi retrieved successfully')
    except Exception as e:
        logger.exception(f"Error listing syllabi: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve syllabi', 500)


@bp.route('/<int:syllabus_id>', methods=['GET'])
@token_required
def get_syllabus(syllabus_id: int) -> Tuple[Response, int]:
    """
    Get syllabus by id
    ---
    get:
      summary: Get syllabus by id
      security:
        - Bearer: []
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus
      tags:
        - Syllabi
      responses:
        200:
          description: Syllabus object
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabus retrieved successfully"
        404:
          description: Syllabus not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        syllabus = syllabus_service.get_syllabus_by_id(syllabus_id)
        if not syllabus:
            return not_found_response('Syllabus not found')
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus retrieved successfully')
    except Exception as e:
        logger.exception(f"Error getting syllabus {syllabus_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve syllabus', 500)


@bp.route('/', methods=['POST'])
@token_required
@role_required(ROLE_LECTURER)
def create_draft() -> Tuple[Response, int]:
    """
    Create a new syllabus draft
    ---
    post:
      summary: Create a new syllabus draft (LECTURER only)
      security:
        - Bearer: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - subject_id
                - program_id
              properties:
                subject_id:
                  type: integer
                  example: 1
                program_id:
                  type: integer
                  example: 1
      tags:
        - Syllabi
      responses:
        201:
          description: Syllabus created successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/SyllabusCreateResponse'
                  message:
                    type: string
                    example: "Syllabus draft created successfully"
        400:
          description: Invalid input
        401:
          description: Unauthorized
        403:
          description: Forbidden - Only LECTURER can create syllabus
    """
    db = get_db_session()
    try:
        # Get owner_lecturer_id from JWT token (current user)
        user_id = get_user_id_from_token()
        if not user_id:
            return error_response('User not authenticated', 401)
        
        syllabus_service = container.syllabus_service(db)
        data = request.get_json()
        
        # Validate request schema
        errors = create_schema.validate(data)
        if errors:
            return validation_error_response(errors)
        
        # Extract and validate required fields
        subject_id = data.get('subject_id')
        program_id = data.get('program_id')
        
        if not subject_id or not program_id:
            return validation_error_response({
                'subject_id': ['This field is required'],
                'program_id': ['This field is required']
            })
        
        # Create syllabus draft - owner is taken from JWT token
        syllabus = syllabus_service.create_draft(
            subject_id=subject_id,
            program_id=program_id,
            owner_lecturer_id=user_id  # From JWT token
        )
        
        # Return response with draft_version_id
        response_data = {
            'syllabus_id': syllabus.syllabus_id,
            'draft_version_id': syllabus.current_version_id  # This is the draft version created
        }
        
        return success_response(data=response_data, message='Syllabus draft created successfully', status_code=201)
    
    except ValidationException as e:
        return error_response(str(e), 400)
    
    except ValueError as e:
        # Handle "not found" errors (subject/program/user)
        error_msg = str(e).lower()
        if 'not found' in error_msg:
            # Determine which resource is not found
            if 'subject' in error_msg:
                return not_found_response(f'Subject with ID {subject_id} not found')
            elif 'program' in error_msg:
                return not_found_response(f'Program with ID {program_id} not found')
            elif 'user' in error_msg:
                return not_found_response(f'User with ID {user_id} not found')
            else:
                return not_found_response(str(e))
        # Other ValueError (e.g., constraint violation)
        return error_response(str(e), 400)
    
    except UnauthorizedException as e:
        return error_response(str(e), 403)
    
    except IntegrityError as e:
        # This should be caught by service layer, but handle as fallback
        logger.exception(f"IntegrityError in create_draft endpoint: {e}")
        error_str = str(e).lower()
        if 'subject' in error_str:
            return not_found_response(f'Subject with ID {subject_id} not found')
        elif 'program' in error_str:
            return not_found_response(f'Program with ID {program_id} not found')
        elif 'user' in error_str:
            return not_found_response(f'User with ID {user_id} not found')
        else:
            return error_response('Database constraint violation', 400)
    
    except Exception as e:
        logger.exception(f"Error creating syllabus draft: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to create syllabus draft', 500)


@bp.route('/<int:syllabus_id>', methods=['PUT'])
@token_required
@role_required(ROLE_LECTURER)
def update_draft(syllabus_id: int) -> Tuple[Response, int]:
    """
    Update a syllabus draft
    ---
    put:
      summary: Update a syllabus draft
      security:
        - Bearer: []
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - reason
              properties:
                reason:
                  type: string
                  description: Reason for rejection (required)
                  example: "Please revise section 3.2"
      tags:
        - Syllabi
      responses:
        200:
          description: Syllabus updated successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabus draft updated successfully"
        400:
          description: Invalid input
        404:
          description: Syllabus not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        user_id = get_user_id_from_token()
        if not user_id:
            return error_response('User not authenticated', 401)
        
        data = request.get_json()
        errors = update_schema.validate(data)
        if errors:
            return validation_error_response(errors)
        
        # Service layer will validate owner and status
        # Don't allow changing owner_lecturer_id - it's fixed from creation
        # Only allow updating subject_id and program_id
        syllabus = syllabus_service.update_draft(
            syllabus_id=syllabus_id,
            subject_id=data.get('subject_id'),
            program_id=data.get('program_id'),
            owner_lecturer_id=user_id  # Pass user_id for owner validation in service
        )
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus draft updated successfully')
    except ValidationException as e:
        # Status validation errors -> 409 Conflict
        error_msg = str(e).lower()
        if 'status' in error_msg or 'draft' in error_msg:
            return error_response(str(e), 409)
        return error_response(str(e), 400)
    except UnauthorizedException as e:
        return error_response(str(e), 403)
    except ValueError as e:
        # ValueError from service usually means "not found"
        error_msg = str(e).lower()
        if 'not found' in error_msg:
            return not_found_response(str(e))
        return error_response(str(e), 400)
    except Exception as e:
        logger.exception(f"Error updating syllabus draft {syllabus_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to update syllabus draft', 500)


@bp.route('/<int:syllabus_id>/submit', methods=['POST'])
@token_required
@role_required(ROLE_LECTURER)
def submit_for_review(syllabus_id: int) -> Tuple[Response, int]:
    """
    Submit syllabus for review
    ---
    post:
      summary: Submit syllabus for review (DRAFT -> PENDING_REVIEW)
      security:
        - Bearer: []
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus
      tags:
        - Syllabi
      responses:
        200:
          description: Syllabus submitted successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabus retrieved successfully"
        400:
          description: Invalid transition
        404:
          description: Syllabus not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        user_id = get_user_id_from_token()
        if not user_id:
            return error_response('User not authenticated', 401)
        
        user_roles = get_user_roles(user_id, db)
        # Use first role (LECTURER should be the primary role for this action)
        role = user_roles[0] if user_roles else ROLE_LECTURER
        
        # Submit for review - validate owner + DRAFT status
        syllabus = syllabus_service.submit_for_review(syllabus_id, role, user_id=user_id)
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus submitted for review successfully')
    except ValidationException as e:
        return error_response(str(e), 400)
    except ValueError as e:
        # ValueError from service usually means "not found"
        error_msg = str(e).lower()
        if 'not found' in error_msg:
            return not_found_response(str(e))
        return error_response(str(e), 400)
    except Exception as e:
        logger.exception(f"Error submitting syllabus for review {syllabus_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to submit syllabus for review', 500)


@bp.route('/reviews/hod/pending', methods=['GET'])
@token_required
@role_required(ROLE_HOD)
def hod_pending_reviews() -> Tuple[Response, int]:
    """
    Get list of syllabi pending HOD review
    ---
    get:
      summary: Get list of syllabi with status PENDING_REVIEW
      security:
        - Bearer: []
      tags:
        - Syllabi
      responses:
        200:
          description: List of pending reviews
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Pending reviews retrieved successfully"
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        # Get all syllabi with PENDING_REVIEW status
        pending_syllabi = syllabus_service.list_syllabi_by_status('PENDING_REVIEW')
        syllabi_data = response_schema.dump(pending_syllabi, many=True)
        return success_response(data=syllabi_data, message='Pending reviews retrieved successfully')
    except Exception as e:
        logger.exception(f"Error listing pending reviews: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve pending reviews', 500)


@bp.route('/syllabus-versions/<int:version_id>', methods=['GET'])
@token_required
def get_syllabus_version(version_id: int) -> Tuple[Response, int]:
    """
    Get syllabus version detail
    ---
    get:
      summary: Get detailed information about a syllabus version
      security:
        - Bearer: []
      parameters:
        - name: version_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus version
      tags:
        - Syllabi
      responses:
        200:
          description: Syllabus version detail
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    type: object
                    properties:
                      version_id:
                        type: integer
                      syllabus_id:
                        type: integer
                      academic_year:
                        type: string
                      version_no:
                        type: integer
                      workflow_status:
                        type: string
                      submitted_at:
                        type: string
                        format: date-time
                      created_at:
                        type: string
                        format: date-time
                      created_by:
                        type: integer
                      syllabus:
                        $ref: '#/components/schemas/SyllabusResponse'
        404:
          description: Version not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        user_id = get_user_id_from_token()
        user_roles = get_user_roles(user_id, db) if user_id else []
        
        version_info = syllabus_service.get_version_detail(
            version_id=version_id,
            user_id=user_id,
            user_roles=user_roles
        )
        if not version_info:
            return not_found_response(f'Syllabus version {version_id} not found')
        return success_response(data=version_info, message='Syllabus version retrieved successfully')
    except UnauthorizedException as e:
        return error_response(str(e), 403)
    except ValueError as e:
        # ValueError from service may be "not found" (for students) or other validation
        error_msg = str(e).lower()
        if 'not found' in error_msg:
            return not_found_response(str(e))
        return error_response(str(e), 400)
    except Exception as e:
        logger.exception(f"Error getting syllabus version {version_id}: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve syllabus version', 500)


@bp.route('/<int:syllabus_id>/hod/approve', methods=['POST'])
@token_required
@role_required(ROLE_HOD)
def hod_approve(syllabus_id: int) -> Tuple[Response, int]:
    """
    HOD approve syllabus
    ---
    post:
      summary: HOD approve syllabus (PENDING_REVIEW -> PENDING_APPROVAL)
      security:
        - Bearer: []
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus
      tags:
        - Syllabi
      responses:
        200:
          description: Syllabus approved by HOD
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabus retrieved successfully"
        400:
          description: Invalid transition
        404:
          description: Syllabus not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        user_id = get_user_id_from_token()
        user_roles = get_user_roles(user_id, db)
        role = user_roles[0] if user_roles else ROLE_HOD
        syllabus = syllabus_service.hod_approve(syllabus_id, role)
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus approved by HOD successfully')
    except ValidationException as e:
        return error_response(str(e), 400)
    except ValueError as e:
        # ValueError from service usually means "not found"
        error_msg = str(e).lower()
        if 'not found' in error_msg:
            return not_found_response(str(e))
        return error_response(str(e), 400)
    except Exception as e:
        logger.exception(f"Error in HOD approve {syllabus_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to approve syllabus', 500)


@bp.route('/<int:syllabus_id>/hod/reject', methods=['POST'])
@token_required
@role_required(ROLE_HOD)
def hod_reject(syllabus_id: int) -> Tuple[Response, int]:
    """
    HOD reject syllabus
    ---
    post:
      summary: HOD reject syllabus (PENDING_REVIEW -> DRAFT)
      security:
        - Bearer: []
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus
      tags:
        - Syllabi
      responses:
        200:
          description: Syllabus rejected by HOD
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabus retrieved successfully"
        400:
          description: Invalid transition
        404:
          description: Syllabus not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        user_id = get_user_id_from_token()
        user_roles = get_user_roles(user_id, db)
        role = user_roles[0] if user_roles else ROLE_HOD
        
        # Get rejection reason from request body
        data = request.get_json() or {}
        reason = data.get('reason', '').strip()
        
        if not reason:
            return validation_error_response({
                'reason': ['Rejection reason is required']
            })
        
        syllabus = syllabus_service.hod_reject(syllabus_id, role, reason=reason)
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus rejected by HOD successfully')
    except ValidationException as e:
        return error_response(str(e), 400)
    except ValueError as e:
        # ValueError from service usually means "not found"
        error_msg = str(e).lower()
        if 'not found' in error_msg:
            return not_found_response(str(e))
        return error_response(str(e), 400)
    except Exception as e:
        logger.exception(f"Error in HOD reject {syllabus_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to reject syllabus', 500)


@bp.route('/reviews/aa/pending', methods=['GET'])
@token_required
@role_required(ROLE_AA)
def aa_pending_reviews() -> Tuple[Response, int]:
    """
    Get list of syllabi pending AA review
    ---
    get:
      summary: Get list of syllabi with status PENDING_APPROVAL
      security:
        - Bearer: []
      tags:
        - Syllabi
      responses:
        200:
          description: List of pending reviews
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Pending reviews retrieved successfully"
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        # Get all syllabi with PENDING_APPROVAL status
        pending_syllabi = syllabus_service.list_syllabi_by_status('PENDING_APPROVAL')
        syllabi_data = response_schema.dump(pending_syllabi, many=True)
        return success_response(data=syllabi_data, message='Pending reviews retrieved successfully')
    except Exception as e:
        logger.exception(f"Error listing pending reviews: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve pending reviews', 500)


@bp.route('/<int:syllabus_id>/aa/approve', methods=['POST'])
@token_required
@role_required(ROLE_AA)
def aa_approve(syllabus_id: int) -> Tuple[Response, int]:
    """
    AA approve syllabus
    ---
    post:
      summary: AA approve syllabus (PENDING_APPROVAL -> APPROVED)
      security:
        - Bearer: []
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus
      tags:
        - Syllabi
      responses:
        200:
          description: Syllabus approved by AA
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabus retrieved successfully"
        400:
          description: Invalid transition
        404:
          description: Syllabus not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        user_id = get_user_id_from_token()
        user_roles = get_user_roles(user_id, db)
        role = user_roles[0] if user_roles else ROLE_AA
        
        # Approve - validate PENDING_APPROVAL status
        syllabus = syllabus_service.aa_approve(syllabus_id, role)
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus approved by AA successfully')
    except ValidationException as e:
        return error_response(str(e), 400)
    except ValueError as e:
        # ValueError from service usually means "not found"
        error_msg = str(e).lower()
        if 'not found' in error_msg:
            return not_found_response(str(e))
        return error_response(str(e), 400)
    except Exception as e:
        logger.exception(f"Error in AA approve {syllabus_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to approve syllabus', 500)


@bp.route('/<int:syllabus_id>/aa/reject', methods=['POST'])
@token_required
@role_required(ROLE_AA)
def aa_reject(syllabus_id: int) -> Tuple[Response, int]:
    """
    AA reject syllabus
    ---
    post:
      summary: AA reject syllabus (PENDING_APPROVAL -> DRAFT)
      security:
        - Bearer: []
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus
      tags:
        - Syllabi
      responses:
        200:
          description: Syllabus rejected by AA
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabus retrieved successfully"
        400:
          description: Invalid transition
        404:
          description: Syllabus not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        user_id = get_user_id_from_token()
        user_roles = get_user_roles(user_id, db)
        role = user_roles[0] if user_roles else ROLE_AA
        
        # Get rejection reason from request body
        data = request.get_json() or {}
        reason = data.get('reason', '').strip()
        
        if not reason:
            return validation_error_response({
                'reason': ['Rejection reason is required']
            })
        
        # Reject - validate PENDING_APPROVAL status + require reason
        syllabus = syllabus_service.aa_reject(syllabus_id, role, reason=reason)
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus rejected by AA successfully')
    except ValidationException as e:
        return error_response(str(e), 400)
    except ValueError as e:
        # ValueError from service usually means "not found"
        error_msg = str(e).lower()
        if 'not found' in error_msg:
            return not_found_response(str(e))
        return error_response(str(e), 400)
    except Exception as e:
        logger.exception(f"Error in AA reject {syllabus_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to reject syllabus', 500)


@bp.route('/reviews/principal/pending', methods=['GET'])
@token_required
@role_required(ROLE_PRINCIPAL)
def principal_pending_reviews() -> Tuple[Response, int]:
    """
    Get list of syllabi pending Principal review (APPROVED status)
    ---
    get:
      summary: Get list of syllabi with status APPROVED (ready to publish)
      security:
        - Bearer: []
      tags:
        - Syllabi
      responses:
        200:
          description: List of pending reviews
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Pending reviews retrieved successfully"
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        # Get all syllabi with APPROVED status
        pending_syllabi = syllabus_service.list_syllabi_by_status('APPROVED')
        syllabi_data = response_schema.dump(pending_syllabi, many=True)
        return success_response(data=syllabi_data, message='Pending reviews retrieved successfully')
    except Exception as e:
        logger.exception(f"Error listing pending reviews: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve pending reviews', 500)


@bp.route('/<int:syllabus_id>/publish', methods=['POST'])
@token_required
@role_required(ROLE_ADMIN, ROLE_PRINCIPAL)
def publish(syllabus_id: int) -> Tuple[Response, int]:
    """
    Publish syllabus
    ---
    post:
      summary: Publish syllabus (APPROVED -> PUBLISHED)
      security:
        - Bearer: []
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus
      tags:
        - Syllabi
      responses:
        200:
          description: Syllabus published successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabus retrieved successfully"
        400:
          description: Invalid transition
        404:
          description: Syllabus not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        user_id = get_user_id_from_token()
        user_roles = get_user_roles(user_id, db)
        # Use PRINCIPAL if available, otherwise ADMIN, otherwise first role
        if ROLE_PRINCIPAL in user_roles:
            role = ROLE_PRINCIPAL
        elif ROLE_ADMIN in user_roles:
            role = ROLE_ADMIN
        else:
            role = user_roles[0] if user_roles else ROLE_ADMIN
        syllabus = syllabus_service.publish(syllabus_id, role)
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus published successfully')
    except ValidationException as e:
        return error_response(str(e), 400)
    except ValueError as e:
        # ValueError from service usually means "not found"
        error_msg = str(e).lower()
        if 'not found' in error_msg:
            return not_found_response(str(e))
        return error_response(str(e), 400)
    except Exception as e:
        logger.exception(f"Error publishing syllabus {syllabus_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to publish syllabus', 500)


@bp.route('/<int:syllabus_id>/unpublish', methods=['POST'])
@token_required
@role_required(ROLE_ADMIN, ROLE_PRINCIPAL)
def unpublish(syllabus_id: int) -> Tuple[Response, int]:
    """
    Unpublish syllabus
    ---
    post:
      summary: Unpublish syllabus (PUBLISHED -> APPROVED)
      security:
        - Bearer: []
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus
      tags:
        - Syllabi
      responses:
        200:
          description: Syllabus unpublished successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabus retrieved successfully"
        400:
          description: Invalid transition
        404:
          description: Syllabus not found
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        user_id = get_user_id_from_token()
        user_roles = get_user_roles(user_id, db)
        # Use PRINCIPAL if available, otherwise ADMIN, otherwise first role
        if ROLE_PRINCIPAL in user_roles:
            role = ROLE_PRINCIPAL
        elif ROLE_ADMIN in user_roles:
            role = ROLE_ADMIN
        else:
            role = user_roles[0] if user_roles else ROLE_ADMIN
        syllabus = syllabus_service.unpublish(syllabus_id, role)
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus unpublished successfully')
    except ValidationException as e:
        return error_response(str(e), 400)
    except ValueError as e:
        # ValueError from service usually means "not found"
        error_msg = str(e).lower()
        if 'not found' in error_msg:
            return not_found_response(str(e))
        return error_response(str(e), 400)
    except Exception as e:
        logger.exception(f"Error unpublishing syllabus {syllabus_id}: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to unpublish syllabus', 500)


@bp.route('/public', methods=['GET'])
def list_published_syllabi() -> Tuple[Response, int]:
    """
    Get all published syllabi (Public endpoint - no authentication required)
    ---
    get:
      summary: Get all published syllabi (Public/Student access)
      tags:
        - Syllabi
      parameters:
        - name: search
          in: query
          required: false
          schema:
            type: string
          description: Search term (searches in subject name, program name)
        - name: page
          in: query
          required: false
          schema:
            type: integer
            default: 1
          description: Page number
        - name: per_page
          in: query
          required: false
          schema:
            type: integer
            default: 20
          description: Items per page
      responses:
        200:
          description: List of published syllabi
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Published syllabi retrieved successfully"
        500:
          description: Internal server error
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        syllabi = syllabus_service.list_published()
        
        # Basic search filtering (can be enhanced)
        search_term = request.args.get('search', '').strip().lower()
        if search_term:
            # Filter by subject/program name (simplified - would need joins in real implementation)
            # For now, return all published
            pass
        
        syllabi_data = response_schema.dump(syllabi, many=True)
        return success_response(data=syllabi_data, message='Published syllabi retrieved successfully')
    except Exception as e:
        logger.exception(f"Error listing published syllabi: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve published syllabi', 500)


@bp.route('/public/<int:syllabus_id>', methods=['GET'])
def get_published_syllabus(syllabus_id: int) -> Tuple[Response, int]:
    """
    Get published syllabus by id (Public endpoint - no authentication required)
    ---
    get:
      summary: Get published syllabus by id (Public/Student access)
      tags:
        - Syllabi
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus
      responses:
        200:
          description: Published syllabus object
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabus retrieved successfully"
        404:
          description: Syllabus not found or not published
        500:
          description: Internal server error
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        syllabus = syllabus_service.get_syllabus_by_id(syllabus_id)
        
        if not syllabus:
            return not_found_response('Syllabus not found')
        
        # Only return if published
        if syllabus.lifecycle_status != 'PUBLISHED':
            return not_found_response('Syllabus is not published')
        
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus retrieved successfully')
    except Exception as e:
        logger.exception(f"Error getting published syllabus {syllabus_id}: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve syllabus', 500)


@bp.route('/<int:syllabus_id>/versions/<int:version_id>/workflow', methods=['GET'])
@token_required
def get_version_workflow(syllabus_id: int, version_id: int) -> Tuple[Response, int]:
    """
    Get workflow information for a syllabus version.
    ---
    get:
      summary: Get workflow progress information for a syllabus version
      security:
        - Bearer: []
      tags:
        - Syllabi
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus
        - name: version_id
          in: path
          required: true
          schema:
            type: integer
          description: ID of the syllabus version
      responses:
        200:
          description: Workflow information retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    type: object
                    properties:
                      version_id:
                        type: integer
                        example: 123
                      current_status:
                        type: string
                        example: "PENDING_APPROVAL"
                      steps:
                        type: array
                        items:
                          type: object
                          properties:
                            code:
                              type: string
                              example: "DRAFT"
                            label:
                              type: string
                              example: "Draft"
                            order:
                              type: integer
                              example: 1
                      current_step_index:
                        type: integer
                        example: 2
                  message:
                    type: string
                    example: "Workflow information retrieved successfully"
        403:
          description: Forbidden - Student role cannot access workflow information
        404:
          description: Syllabus version not found
        500:
          description: Internal server error
    """
    db = get_db_session()
    try:
        # Authorization: Block STUDENT role
        user_id = get_user_id_from_token()
        if not user_id:
            return error_response('User not authenticated', 401)
        
        user_roles = get_user_roles(user_id, db)
        if ROLE_STUDENT in user_roles:
            return error_response(
                'Students cannot access workflow information',
                403
            )
        
        # Get workflow info from service
        syllabus_service = container.syllabus_service(db)
        workflow_info = syllabus_service.get_version_workflow_info(version_id)
        
        if not workflow_info:
            return not_found_response(f'Syllabus version {version_id} not found')
        
        return success_response(
            data=workflow_info,
            message='Workflow information retrieved successfully'
        )
        
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return not_found_response(error_msg)
        return error_response(error_msg, 400)
    except Exception as e:
        logger.exception(f"Error getting workflow info for version {version_id}: {e}")
        return error_response('Failed to retrieve workflow information', 500)

