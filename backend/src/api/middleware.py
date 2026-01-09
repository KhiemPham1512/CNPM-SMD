# Middleware functions for processing requests and responses

import logging

from flask import jsonify, request

logger = logging.getLogger(__name__)


def log_request_info(app):
    """Log request information for debugging."""
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())


def handle_options_request():
    """Handle OPTIONS preflight requests."""
    return jsonify({'message': 'CORS preflight response'}), 200


def add_custom_headers(response):
    """Add custom headers to response."""
    response.headers['X-Custom-Header'] = 'Value'
    return response


def middleware(app):
    """Register middleware functions with Flask app."""
    @app.before_request
    def before_request():
        # Skip logging for Swagger endpoints to reduce noise
        if request.path in ['/swagger.json', '/docs', '/docs/'] or request.path.startswith('/docs/'):
            return
        log_request_info(app)

    @app.after_request
    def after_request(response):
        return add_custom_headers(response)

    # Only handle specific exceptions, not all Exception
    # Let Flask handle other exceptions with its default handlers
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors."""
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors."""
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({'error': 'Method not allowed'}), 405

    @app.route('/options', methods=['OPTIONS'])
    def options_route():
        return handle_options_request()
