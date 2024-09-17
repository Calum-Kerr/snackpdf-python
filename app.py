from flask import Flask, request
from pdf_to_image import create_app
import logging
import traceback

app = create_app()

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def catch_all(path):
    print(f"Accessed path: {path}")
    print(f"Method: {request.method}")
    print(f"URL: {request.url}")
    return f"You tried to reach {path} with method {request.method}, but it doesn't exist or the method is not allowed.", 405


# Example error handler to catch unhandled exceptions globally
@app.errorhandler(Exception)
def handle_exception(e):
    # You can log the full stack trace here using the logging module
    error_trace = traceback.format_exc()
    logging.error(f"An error occurred: {str(e)}")
    logging.error(f"Full stack trace:\n{error_trace}")
    
    # You can return a custom message with the stack trace (optional, better for development only)
    return f"An error occurred: {str(e)}\n\nFull Traceback:\n{error_trace}", 500


if __name__ == '__main__':
    # Enable debugging mode
    app.run(debug=True)
