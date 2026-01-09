import logging
from typing import Tuple

from flask import Blueprint, Response, jsonify, request

from api.schemas.syllabus import SyllabusCreateSchema, SyllabusResponseSchema, SyllabusUpdateSchema
from api.responses import success_response, error_response, not_found_response, validation_error_response
from api.utils.authz import get_user_id_from_token, get_user_roles, role_required, token_required
from api.utils.db import get_db_session
from dependency_container import container
from domain.exceptions import ValidationException

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
    Get all syllabi
    ---
    get:
      summary: Get all syllabi
      security:
        - Bearer: []
      tags:
        - Syllabi
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
def create_draft() -> Tuple[Response, int]:
    """
    Create a new syllabus draft
    ---
    post:
      summary: Create a new syllabus draft
      security:
        - Bearer: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SyllabusCreate'
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
                    $ref: '#/components/schemas/SyllabusResponse'
                  message:
                    type: string
                    example: "Syllabus draft created successfully"
        400:
          description: Invalid input
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        data = request.get_json()
        errors = create_schema.validate(data)
        if errors:
            return validation_error_response(errors)
        
        syllabus = syllabus_service.create_draft(
            subject_id=data['subject_id'],
            program_id=data['program_id'],
            owner_lecturer_id=data['owner_lecturer_id']
        )
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus draft created successfully', status_code=201)
    except ValidationException as e:
        return error_response(str(e), 400)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.exception(f"Error creating syllabus draft: {e}")
        # Check if it's a database connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to create syllabus draft', 500)


@bp.route('/<int:syllabus_id>', methods=['PUT'])
@token_required
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
              $ref: '#/components/schemas/SyllabusUpdate'
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
        data = request.get_json()
        errors = update_schema.validate(data)
        if errors:
            return validation_error_response(errors)
        
        syllabus = syllabus_service.update_draft(
            syllabus_id=syllabus_id,
            subject_id=data.get('subject_id'),
            program_id=data.get('program_id'),
            owner_lecturer_id=data.get('owner_lecturer_id')
        )
        syllabus_data = response_schema.dump(syllabus)
        return success_response(data=syllabus_data, message='Syllabus draft updated successfully')
    except ValidationException as e:
        return error_response(str(e), 400)
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
        user_roles = get_user_roles(user_id, db)
        # Use first role (LECTURER should be the primary role for this action)
        role = user_roles[0] if user_roles else ROLE_LECTURER
        syllabus = syllabus_service.submit_for_review(syllabus_id, role)
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
        syllabus = syllabus_service.hod_reject(syllabus_id, role)
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
      summary: AA reject syllabus (PENDING_APPROVAL -> PENDING_REVIEW)
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
        syllabus = syllabus_service.aa_reject(syllabus_id, role)
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

