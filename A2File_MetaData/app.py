# project2_file_metadata/app.py
"""
File Metadata & Storage Service
- Upload files, save securely, return metadata
- List all uploaded files
- Delete files
- No secrets needed – safe for GitHub
"""

import os
import json
import mimetypes
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf', 'zip'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# File for storing metadata (to persist between server restarts)
METADATA_FILE = 'file_metadata.json'

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_metadata():
    """Load metadata from JSON file."""
    if not os.path.exists(METADATA_FILE):
        return {}
    with open(METADATA_FILE, 'r') as f:
        return json.load(f)

def save_metadata(metadata):
    """Save metadata to JSON file."""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

# -------------------- API Endpoints --------------------

# 1. Upload a file
@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload a single file. Returns metadata."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    
    # Secure filename and generate unique name to avoid collisions
    original_filename = file.filename
    safe_filename = secure_filename(original_filename)
    # Add timestamp to make unique
    name_parts = safe_filename.rsplit('.', 1)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}" if len(name_parts) > 1 else f"{safe_filename}_{timestamp}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Save file
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    mime_type = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
    
    # Prepare metadata
    metadata = {
        "original_name": original_filename,
        "saved_name": unique_filename,
        "size_bytes": file_size,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "mime_type": mime_type,
        "upload_time": datetime.now().isoformat(),
        "path": filepath
    }
    
    # Store in central metadata store
    all_metadata = load_metadata()
    all_metadata[unique_filename] = metadata
    save_metadata(all_metadata)
    
    return jsonify({"message": "File uploaded", "metadata": metadata}), 201

# 2. List all uploaded files (metadata only)
@app.route('/files', methods=['GET'])
def list_files():
    """Return list of all uploaded files with metadata."""
    all_metadata = load_metadata()
    return jsonify(list(all_metadata.values())), 200

# 3. Get metadata of a specific file by saved name
@app.route('/files/<saved_name>', methods=['GET'])
def get_file_metadata(saved_name):
    """Get metadata of a single file."""
    all_metadata = load_metadata()
    if saved_name not in all_metadata:
        return jsonify({"error": "File not found"}), 404
    return jsonify(all_metadata[saved_name]), 200

# 4. Download a file by saved name
@app.route('/download/<saved_name>', methods=['GET'])
def download_file(saved_name):
    """Serve the file for download."""
    all_metadata = load_metadata()
    if saved_name not in all_metadata:
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], saved_name, as_attachment=True)

# 5. Delete a file by saved name
@app.route('/files/<saved_name>', methods=['DELETE'])
def delete_file(saved_name):
    """Delete file from storage and metadata."""
    all_metadata = load_metadata()
    if saved_name not in all_metadata:
        return jsonify({"error": "File not found"}), 404
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_name)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    del all_metadata[saved_name]
    save_metadata(all_metadata)
    return '', 204

# 6. (Bonus) Get file by original name? Not implemented because multiple files can have same original name

if __name__ == '__main__':
    # Ensure metadata file exists
    if not os.path.exists(METADATA_FILE):
        save_metadata({})
    app.run(debug=True, port=5000)