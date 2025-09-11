import uuid
from pathlib import Path
from flask import Flask, request, jsonify, Response, send_from_directory, render_template

# Import the core logic from our backend file
import backend

# --- Configuration ---
app = Flask(__name__)

# --- API Endpoints ---

@app.route("/")
def index():
    """Serves the main HTML user interface from the templates folder."""
    return render_template('index.html')

@app.route("/outputs/<filename>")
def get_output_file(filename):
    """Serves the generated PDF files from the output directory."""
    return send_from_directory(backend.OUTPUT_DIR, filename)

@app.route("/flowchart/templates", methods=["GET"])
def list_templates():
    """Lists available flowchart templates."""
    templates = []
    # Ensure template directory exists before trying to list files
    if backend.TEMPLATE_DIR.exists():
        for f in backend.TEMPLATE_DIR.glob("*.dot"):
            # Format the name for display, e.g., 'simple_process.dot' -> 'Simple Process'
            display_name = f.stem.replace("_", " ").title()
            templates.append({"id": f.stem, "name": display_name})
    return jsonify(templates)

@app.route("/flowchart/load_template", methods=["POST"])
def handle_load_template_request():
    """Endpoint to load a pre-defined flowchart template."""
    if not request.json or "user_email" not in request.json or "template_id" not in request.json:
        return jsonify({"error": "Request body must include 'user_email' and 'template_id'"}), 400

    user_email = request.json["user_email"]
    template_id = request.json["template_id"]

    # Validate template_id to prevent directory traversal
    template_file = backend.TEMPLATE_DIR / f"{template_id}.dot"
    if not template_file.is_file():
            return jsonify({"error": f"Template '{template_id}' not found."}), 404
    
    try:
        dot_code = template_file.read_text()
    except Exception as e:
        return jsonify({"error": f"Could not read template file: {e}"}), 500

    # Create a new session for the user
    user_folder_name = backend.sanitize_email_for_folder(user_email)
    user_session_dir = backend.SESSION_DIR / user_folder_name
    user_session_dir.mkdir(parents=True, exist_ok=True)
    session_id = str(uuid.uuid4())
    session_file = user_session_dir / f"{session_id}.dot"

    # Process the DOT code directly
    output_filename, error_msg = backend.process_dot_code(dot_code, session_file)

    if error_msg:
        return jsonify({"error": error_msg}), 500

    return jsonify({
        "status": "success",
        "user_email": user_email,
        "session_id": session_id,
        "message": f"Template '{template_id}' loaded successfully.",
        "output_filename": output_filename
    }), 200

@app.route("/flowchart/create", methods=["POST"])
def handle_create_request():
    """Endpoint to start a new flowchart conversation for a specific user."""
    if not request.json or "user_email" not in request.json or "prompt" not in request.json:
        return jsonify({"error": "Request body must include 'user_email' and 'prompt'"}), 400

    user_email = request.json["user_email"]
    user_prompt = request.json["prompt"]
    
    user_folder_name = backend.sanitize_email_for_folder(user_email)
    user_session_dir = backend.SESSION_DIR / user_folder_name
    user_session_dir.mkdir(parents=True, exist_ok=True)

    session_id = str(uuid.uuid4())
    session_file = user_session_dir / f"{session_id}.dot"

    output_filename, error_msg = backend.process_flowchart_request(user_prompt, session_file, is_new=True)

    if error_msg:
        return jsonify({"error": error_msg}), 500

    return jsonify({
        "status": "success",
        "user_email": user_email,
        "session_id": session_id,
        "message": "New flowchart PDF created.",
        "output_filename": output_filename
    }), 200

@app.route("/flowchart/add", methods=["POST"])
def handle_add_request():
    """Endpoint to add a step to an existing flowchart for a specific user."""
    if not request.json or "user_email" not in request.json or "session_id" not in request.json or "prompt" not in request.json:
        return jsonify({"error": "Request body must include 'user_email', 'session_id', and 'prompt'"}), 400

    user_email = request.json["user_email"]
    session_id = request.json["session_id"]
    user_prompt = request.json["prompt"]

    user_folder_name = backend.sanitize_email_for_folder(user_email)
    session_file = backend.SESSION_DIR / user_folder_name / f"{session_id}.dot"
    
    if not session_file.exists():
        return jsonify({"error": f"Session ID '{session_id}' not found for user '{user_email}'."}), 404

    output_filename, error_msg = backend.process_flowchart_request(user_prompt, session_file, is_new=False)

    if error_msg:
        return jsonify({"error": error_msg}), 500

    return jsonify({
        "status": "success",
        "user_email": user_email,
        "session_id": session_id,
        "message": "Flowchart PDF updated.",
        "output_filename": output_filename
    }), 200

# --- Main Execution ---
if __name__ == "__main__":
    # The 'ssl_context="adhoc"' argument enables HTTPS for microphone access
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context="adhoc")