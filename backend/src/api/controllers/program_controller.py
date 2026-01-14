import logging
from typing import Tuple

from flask import Blueprint, Response

from api.responses import success_response, error_response
from api.utils.db import get_db_session
from infrastructure.models.program import Program

logger = logging.getLogger(__name__)

bp = Blueprint('program', __name__, url_prefix='/programs')


@bp.route('/', methods=['GET'])
def list_programs() -> Tuple[Response, int]:
    """
    Get all programs
    ---
    get:
      summary: Get all programs
      tags:
        - Programs
      responses:
        200:
          description: List of programs
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
                          example: "SE"
                        name:
                          type: string
                          example: "Software Engineering"
                  message:
                    type: string
                    example: "Programs retrieved successfully"
        500:
          description: Internal server error
    """
    db = get_db_session()
    try:
        programs = db.query(Program).all()
        programs_data = [
            {
                'id': program.program_id,
                'code': program.code,
                'name': program.name
            }
            for program in programs
        ]
        return success_response(data=programs_data, message='Programs retrieved successfully')
    except Exception as e:
        logger.exception(f"Error listing programs: {e}")
        error_str = str(e).lower()
        if 'connection' in error_str or 'unavailable' in error_str or 'timeout' in error_str:
            return error_response('Database service temporarily unavailable', 503)
        return error_response('Failed to retrieve programs', 500)
