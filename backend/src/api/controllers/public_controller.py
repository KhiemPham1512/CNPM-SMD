import logging
from typing import Tuple
from flask import Blueprint, Response, request
from api.responses import success_response, error_response, not_found_response, validation_error_response
from api.utils.authz import token_required, get_user_id_from_token
from api.utils.db import get_db_session
from dependency_container import container
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

bp = Blueprint('public', __name__, url_prefix='/public')


@bp.route('/syllabi', methods=['GET'])
def search_syllabi() -> Tuple[Response, int]:
    """
    Search published syllabi (Public endpoint - no authentication required)
    ---
    get:
      summary: Search published syllabi by subject code/name or keyword
      tags:
        - Public
      parameters:
        - name: query
          in: query
          required: false
          schema:
            type: string
          description: Search query (subject code, name, or keyword)
        - name: search
          in: query
          required: false
          schema:
            type: string
          description: Alias for query parameter
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
                      type: object
                  message:
                    type: string
                    example: "Published syllabi retrieved successfully"
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        
        # Get search query from request
        query = request.args.get('query') or request.args.get('search', '').strip()
        
        # Get all published syllabi
        published_syllabi = syllabus_service.list_syllabi_by_status('PUBLISHED')
        
        # Filter by query if provided
        if query:
            query_lower = query.lower()
            filtered = []
            for syllabus in published_syllabi:
                # Search in subject_id, program_id, syllabus_id (as strings)
                if (str(syllabus.subject_id).lower() in query_lower or
                    str(syllabus.program_id).lower() in query_lower or
                    str(syllabus.syllabus_id).lower() in query_lower):
                    filtered.append(syllabus)
            
            published_syllabi = filtered
        
        from api.schemas.syllabus import SyllabusResponseSchema
        response_schema = SyllabusResponseSchema()
        syllabi_data = response_schema.dump(published_syllabi, many=True)
        
        return success_response(data=syllabi_data, message='Published syllabi retrieved successfully')
    except Exception as e:
        logger.exception(f"Error searching published syllabi: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve published syllabi', 500)


@bp.route('/syllabi/<int:syllabus_id>', methods=['GET'])
def get_public_syllabus(syllabus_id: int) -> Tuple[Response, int]:
    """
    Get published syllabus detail (Public endpoint - no authentication required)
    ---
    get:
      summary: Get published syllabus detail
      tags:
        - Public
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        200:
          description: Published syllabus detail
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
                  message:
                    type: string
                    example: "Published syllabus retrieved successfully"
        404:
          description: Syllabus not found or not published
    """
    db = get_db_session()
    try:
        syllabus_service = container.syllabus_service(db)
        syllabus = syllabus_service.get_by_id(syllabus_id)
        
        if not syllabus:
            return not_found_response('Syllabus not found')
        
        # Only allow viewing PUBLISHED syllabi
        if syllabus.lifecycle_status != 'PUBLISHED':
            return not_found_response('Syllabus is not published')
        
        from api.schemas.syllabus import SyllabusResponseSchema
        response_schema = SyllabusResponseSchema()
        syllabus_data = response_schema.dump(syllabus)
        
        # Add AI Summary placeholder if available
        from infrastructure.models.ai_summary import AISummary
        if syllabus.current_version_id:
            ai_summary = db.query(AISummary).filter_by(
                version_id=syllabus.current_version_id
            ).first()
            if ai_summary:
                syllabus_data['ai_summary'] = {
                    'summary_id': ai_summary.summary_id,
                    'summary_text': ai_summary.summary_text,
                    'generated_at': ai_summary.generated_at.isoformat() if ai_summary.generated_at else None,
                }
            else:
                syllabus_data['ai_summary'] = None
        
        return success_response(data=syllabus_data, message='Published syllabus retrieved successfully')
    except Exception as e:
        logger.exception(f"Error getting public syllabus {syllabus_id}: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve syllabus', 500)


@bp.route('/syllabi/<int:syllabus_id>/subscribe', methods=['POST'])
@token_required
def subscribe_syllabus(syllabus_id: int) -> Tuple[Response, int]:
    """
    Subscribe to syllabus updates (Student/Public - requires authentication)
    ---
    post:
      summary: Subscribe to syllabus updates
      security:
        - Bearer: []
      tags:
        - Public
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        200:
          description: Subscription created successfully
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
                      sub_id:
                        type: integer
                      syllabus_id:
                        type: integer
                      user_id:
                        type: integer
                  message:
                    type: string
                    example: "Subscribed successfully"
        400:
          description: Already subscribed or invalid request
        404:
          description: Syllabus not found or not published
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        user_id = get_user_id_from_token()
        
        # Verify syllabus exists and is published
        syllabus_service = container.syllabus_service(db)
        syllabus = syllabus_service.get_by_id(syllabus_id)
        
        if not syllabus:
            return not_found_response('Syllabus not found')
        
        if syllabus.lifecycle_status != 'PUBLISHED':
            return error_response('Can only subscribe to published syllabi', 400)
        
        # Check if already subscribed
        from infrastructure.models.subscription import Subscription
        existing = db.query(Subscription).filter_by(
            user_id=user_id,
            syllabus_id=syllabus_id
        ).first()
        
        if existing:
            return error_response('Already subscribed to this syllabus', 400)
        
        # Create subscription
        subscription = Subscription(
            user_id=user_id,
            syllabus_id=syllabus_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(subscription)
        db.commit()
        
        return success_response(
            data={
                'sub_id': subscription.sub_id,
                'syllabus_id': subscription.syllabus_id,
                'user_id': subscription.user_id,
            },
            message='Subscribed successfully'
        )
    except IntegrityError:
        db.rollback()
        return error_response('Subscription already exists', 400)
    except Exception as e:
        db.rollback()
        logger.exception(f"Error subscribing to syllabus {syllabus_id}: {e}")
        return error_response('Failed to subscribe', 500)


@bp.route('/syllabi/<int:syllabus_id>/feedback', methods=['POST'])
@token_required
def submit_feedback(syllabus_id: int) -> Tuple[Response, int]:
    """
    Submit feedback for a syllabus (Student/Public - requires authentication)
    ---
    post:
      summary: Submit feedback for a syllabus
      security:
        - Bearer: []
      tags:
        - Public
      parameters:
        - name: syllabus_id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - content
              properties:
                content:
                  type: string
                  description: Feedback content/report
                  example: "Found an error in section 3.2"
                rating:
                  type: integer
                  description: Optional rating (1-5)
                  example: 4
      responses:
        201:
          description: Feedback submitted successfully
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
                      feedback_id:
                        type: integer
                      syllabus_id:
                        type: integer
                      content:
                        type: string
                  message:
                    type: string
                    example: "Feedback submitted successfully"
        400:
          description: Invalid input
        404:
          description: Syllabus not found or not published
        401:
          description: Unauthorized
    """
    db = get_db_session()
    try:
        user_id = get_user_id_from_token()
        data = request.get_json() or {}
        
        if 'content' not in data or not data['content'].strip():
            return validation_error_response({'content': ['Feedback content is required']})
        
        # Verify syllabus exists and is published
        syllabus_service = container.syllabus_service(db)
        syllabus = syllabus_service.get_by_id(syllabus_id)
        
        if not syllabus:
            return not_found_response('Syllabus not found')
        
        if syllabus.lifecycle_status != 'PUBLISHED':
            return error_response('Can only submit feedback for published syllabi', 400)
        
        if not syllabus.current_version_id:
            return error_response('Syllabus has no version', 400)
        
        # Create feedback
        from infrastructure.models.feedback import Feedback
        feedback = Feedback(
            syllabus_id=syllabus_id,
            version_id=syllabus.current_version_id,
            author_user_id=user_id,
            rating=data.get('rating', 0),  # Default 0 if not provided
            content=data['content'].strip(),
            created_at=datetime.now(timezone.utc)
        )
        db.add(feedback)
        db.commit()
        
        return success_response(
            data={
                'feedback_id': feedback.feedback_id,
                'syllabus_id': feedback.syllabus_id,
                'content': feedback.content,
                'rating': feedback.rating,
            },
            message='Feedback submitted successfully',
            status_code=201
        )
    except Exception as e:
        db.rollback()
        logger.exception(f"Error submitting feedback for syllabus {syllabus_id}: {e}")
        return error_response('Failed to submit feedback', 500)
