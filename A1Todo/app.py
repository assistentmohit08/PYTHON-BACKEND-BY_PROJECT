"""
🟢 Project 1 – To-Do List API (CRUD)
This project teaches the core CRUD operations – the foundation of almost every backend.
We will build a REST API for managing tasks (todos).
GET /todos – get all tasks
GET /todos/<id> – get a single task
POST /todos – create a new task
PUT /todos/<id> – replace an existing task
PATCH /todos/<id> – partially update a task
DELETE /todos/<id> – delete a task
Data will be stored in a JSON file (todos.json) to persist between server restarts.
हम एक REST API बनाएँगे जो tasks (काम) को manage करेगी।
GET /todos – सारे tasks दिखाएगा
POST /todos – नया task बनाएगा
PUT /todos/<id> – पूरा task replace करेगा
PATCH /todos/<id> – सिर्फ कुछ fields update करेगा
DELETE /todos/<id> – task delete करेगा
Data एक JSON file में save होगा ताकि server restart होने पर भी data रहे।
"""
# project1_todo_api/app.py
"""
To-Do List REST API
- CRUD operations using Flask
- Persistent storage using JSON file
"""

import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Path to the JSON file that stores todos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "todos.json")

# os.path.abspath(__file__)
# Output:
# C:\Users\Mohit\project1_todo_api\app.py
# -------------------- Helper Functions --------------------

@app.route('/')
def home():
    return "hello todos"

def load_todos():
    """Load todos from JSON file. If file doesn't exist, return empty list."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_todos(todos):
    """Save todos list to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(todos, f, indent=2)

# -------------------- API Endpoints --------------------

# 1. GET /todos - List all todos
@app.route('/todos', methods=['GET'])
def get_todos():
    todos = load_todos()
    return jsonify(todos), 200

# 2. GET /todos/<id> - Get a single todo
@app.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todos = load_todos()
    todo = next((t for t in todos if t.get('id') == todo_id), None)
    if todo is None:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(todo), 200

# 3. POST /todos - Create a new todo
@app.route('/todos', methods=['POST'])
def create_todo():
    todos = load_todos()
    data = request.get_json()
    
    # Validation
    if not data or 'title' not in data:
        return jsonify({"error": "Title is required"}), 400
    
    # Generate new ID (max id + 1, or 1 if empty)
    new_id = max([t['id'] for t in todos], default=0) + 1
    
    new_todo = {
        "id": new_id,
        "title": data['title'],
        "completed": data.get('completed', False)  # default False
    }
    todos.append(new_todo)
    save_todos(todos)
    return jsonify(new_todo), 201  # 201 Created

# 4. PUT /todos/<id> - Full replace (idempotent)
@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo_full(todo_id):
    todos = load_todos()
    data = request.get_json()
    
    if not data or 'title' not in data or 'completed' not in data:
        return jsonify({"error": "Title and completed fields required"}), 400
    
    # Find index
    for i, t in enumerate(todos):
        if t['id'] == todo_id:
            # Full replacement
            todos[i] = {
                "id": todo_id,
                "title": data['title'],
                "completed": data['completed']
            }
            save_todos(todos)
            return jsonify(todos[i]), 200
    
    return jsonify({"error": "Todo not found"}), 404

# 5. PATCH /todos/<id> - Partial update
@app.route('/todos/<int:todo_id>', methods=['PATCH'])
def update_todo_partial(todo_id):
    todos = load_todos()
    data = request.get_json()
    
    for i, t in enumerate(todos):
        if t['id'] == todo_id:
            # Partial update: only change provided fields
            if 'title' in data:
                todos[i]['title'] = data['title']
            if 'completed' in data:
                todos[i]['completed'] = data['completed']
            save_todos(todos)
            return jsonify(todos[i]), 200
    
    return jsonify({"error": "Todo not found"}), 404

# 6. DELETE /todos/<id> - Delete a todo
@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todos = load_todos()
    for i, t in enumerate(todos):
        if t['id'] == todo_id:
            del todos[i]
            save_todos(todos)
            return '', 204  # No Content
    
    return jsonify({"error": "Todo not found"}), 404

# -------------------- Run Server --------------------
if __name__ == '__main__':
    # Ensure data file exists (empty list if needed)
    if not os.path.exists(DATA_FILE):
        save_todos([])
    app.run(debug=True, port=5000)