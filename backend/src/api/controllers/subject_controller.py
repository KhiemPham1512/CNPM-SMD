import logging
from typing import Tuple

from flask import Blueprint, Response

from api.responses import success_response, error_response
from api.utils.db import get_db_session
from infrastructure.models.subject import Subject

logger = logging.getLogger(__name__)

bp = Blueprint('subject', __name__, url_prefix='/subjects')


@bp.route('/', methods=['GET'])
def list_subjects() -> Tuple[Response, int]:
    """
    Get all subjects
    ---
    get:
      summary: Get all subjects
      tags:
        - Subjects
      responses:
        200:
          description: List of subjects
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
                      properties:
                        id:
                          type: integer
                          example: 1
                        code:
                          type: string
                          example: "CNPM"
                        name:
                          type: string
                          example: "Công nghệ phần mềm"
                  message:
                    type: string
                    example: "Subjects retrieved successfully"
        500:
          description: Internal server error
    """
    db = get_db_session()
    try:
        subjects = db.query(Subject).all()
        subjects_data = [
            {
                'id': subject.subject_id,
                'code': subject.code,
                'name': subject.name
            }
            for subject in subjects
        ]
        return success_response(data=subjects_data, message='Subjects retrieved successfully')
    except Exception as e:
        logger.exception(f"Error listing subjects: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve subjects', 500)
