# src/api/responses.py

from flask import jsonify
from typing import Any, Dict, Optional, List


def success_response(data: Any = None, message: str = "Success", status_code: int = 200):
    """
    Standard success response format.
    
    Args:
        data: Response data (can be dict, list, or None)
        message: Success message
        status_code: HTTP status code (default: 200)
    
    Returns:
        JSON response with format: {"success": true, "data": ..., "message": "..."}
    """
    response = {
        "success": True,
        "message": message
    }
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code


def error_response(message: str = "An error occurred", status_code: int = 400, errors: Optional[List] = None):
    """
    Standard error response format.
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        errors: Optional list of validation errors
    
    Returns:
        JSON response with format: {"success": false, "message": "...", "errors": [...]}
    """
    response = {
        "success": False,
        "message": message
    }
    if errors:
        response["errors"] = errors
    return jsonify(response), status_code


def not_found_response(message: str = "Resource not found"):
    """
    Standard 404 response format.
    
    Args:
        message: Not found message
    
    Returns:
        JSON response with format: {"success": false, "message": "..."}
    """
    return error_response(message=message, status_code=404)


def validation_error_response(errors: List, message: str = "Validation errors"):
    """
    Standard validation error response format.
    
    Args:
        errors: List of validation errors
        message: Error message
    
    Returns:
        JSON response with format: {"success": false, "message": "...", "errors": [...]}
    """
    return error_response(message=message, status_code=422, errors=errors)