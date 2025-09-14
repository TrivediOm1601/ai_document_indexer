from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
from functools import wraps
from datetime import datetime
from config import Config
from modules import database, auth, semantic_search
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import magic
from werkzeug.security import generate_password_hash
from modules.upload_handler import handle_file_upload
from flask import session, request, render_template
from datetime import datetime


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Mapping broad categories to detailed categories
BROAD_TO_DETAILED = {
    'Finance': 'Invoice',           # default detailed category for Finance
    'HR': 'Resume',
    'Legal': 'Contract',
    'Technical': 'Technical_Manual',
}

def init_db():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS document_corrections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        old_category TEXT,
        corrected_category TEXT,
        corrected_by INTEGER,
        correction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    limiter = Limiter(
        app,
        key_func=get_remote_address,
        storage_uri="redis://localhost:6379",
        default_limits=["200 per day", "50 per hour"]
    )
    database.init_db()
    init_db()
    
    def allowed_file_magic(stream):
        file_start = stream.read(2048)
        stream.seek(0)
        mime = magic.from_buffer(file_start, mime=True)
        allowed_mimes = {
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX MIME
            'text/plain'
        }
        return mime in allowed_mimes


    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login'))

    @app.route("/status")
    def health():
        return jsonify({"status": "healthy"}), 200

    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    @limiter.limit("10/minute")
    def upload():
        if request.method == 'POST':
            uploaded_file = request.files.get('document')
            if not uploaded_file or uploaded_file.filename == '':
                flash('No file selected', 'warning')
                return redirect(request.url)

            if not allowed_file_magic(uploaded_file.stream):
                flash('Disallowed file type detected.', 'danger')
                return redirect(request.url)

            try:
                doc_id = handle_file_upload(uploaded_file, app.config['UPLOAD_FOLDER'], session['user_id'])
                flash('File uploaded and processed successfully', 'success')
                return redirect(url_for('dashboard'))

            except ValueError as ve:
                flash(str(ve), 'danger')
                return redirect(request.url)

            except Exception as e:
                # Log exception details here as needed
                flash('An unexpected error occurred during upload.', 'danger')
                return redirect(request.url)

        return render_template('upload.html')
    

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')

            if not username or not password or not role:
                flash('All fields are required.', 'warning')
                return render_template('signup.html')

            if role not in ['admin', 'hr', 'finance']:
                flash('Invalid role selected.', 'warning')
                return render_template('signup.html')

            conn = database.get_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                flash('Username already taken.', 'danger')
                conn.close()
                return render_template('signup.html')

            hashed_password = generate_password_hash(password)

            cursor.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                (username, hashed_password, role)
            )
            conn.commit()
            conn.close()

            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))

        return render_template('signup.html')

    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("10 per minute")
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = auth.get_user_by_username(username)
            if user and auth.verify_password(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/document/<int:document_id>')
    @login_required
    def document(document_id):
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
        doc = cursor.fetchone()
        if not doc:
            conn.close()
            abort(404)

        user_role = session.get('role')
        if user_role != 'admin' and doc['category'].lower() != user_role.lower():
            conn.close()
            abort(403)

        # Log view action and close connection
        cursor.execute('INSERT INTO access_logs (user_id, document_id, action, timestamp) VALUES (?, ?, ?, ?)',
                       (session['user_id'], document_id, 'view', datetime.now()))
        conn.commit()
        conn.close()

        return render_template('document.html', document=doc)

    SIMILARITY_THRESHOLD = 0.85  # Set your desired cutoff value

    @app.route('/search', methods=['GET', 'POST'])
    @login_required
    def search():
        results = []
        if request.method == 'POST':
            query = request.form.get('query', '').strip()
            if query:
                try:
                # Get embedding model and generate query embedding
                    model = semantic_search.get_embedding_model()
                    query_embedding = semantic_search.generate_embedding(query, model)

                # Perform vector similarity search
                    search_results = semantic_search.search_index(query_embedding, k=20)

                    if not search_results:
                        flash("No documents found matching the query.", "warning")
                        return render_template('search.html', results=[])

                    doc_ids = [doc_id for doc_id, _ in search_results]

                # Fetch documents from DB in batch
                    conn = database.get_db_connection()
                    cursor = conn.cursor()
                    format_strings = ','.join('?' * len(doc_ids))
                    cursor.execute(f"SELECT * FROM documents WHERE id IN ({format_strings})", tuple(doc_ids))
                    docs = {row['id']: row for row in cursor.fetchall()}
                    conn.close()

                # Prepare (doc, score) list for filtering
                    doc_score_list = [(docs[doc_id], score) for doc_id, score in search_results if doc_id in docs]

                # Check or import keyword_filter if not in semantic_search.py
                # from modules.semantic_search import keyword_filter

                # Apply keyword filter to improve relevance
                    results = semantic_search.keyword_filter(doc_score_list, query)

                # Limit results count if needed
                    results = results[:10]

                # Debug prints (optional)
                    print(f"Raw search count: {len(doc_score_list)}")
                    print(f"Filtered search count: {len(results)}")

                except Exception as e:
                    print(f"Search error: {e}")
                    flash("An error occurred during search. Please try again.", "danger")
                    results = []

        return render_template('search.html', results=results)


    
    @app.route('/document/<int:document_id>/update_category', methods=['POST'])
    @login_required
    def update_category(document_id):
        new_category = request.form.get('category')
        allowed_categories = [
            'Invoice', 'Financial_Report', 'Contract', 'Expense_Report', 'Resume', 'Job_Description',
            'Technical_Manual', 'Research_Paper', 'Non_Relevant'
        ]
        if new_category not in allowed_categories:
            flash('Invalid category selected.', 'danger')
            return redirect(url_for('document', document_id=document_id))

        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE documents SET category = ? WHERE id = ?', (new_category, document_id))
        cursor.execute('SELECT category FROM documents WHERE id = ?', (document_id,))
        old_category = cursor.fetchone()['category']
        cursor.execute('''
        INSERT INTO document_corrections (document_id, old_category, corrected_category, corrected_by)
        VALUES (?, ?, ?, ?)
        ''', (document_id, old_category, new_category, session['user_id']))
        
        conn.commit()
        conn.close()

        flash('Category updated successfully.', 'success')
        return redirect(url_for('document', document_id=document_id))


    @app.route('/dashboard')
    @login_required
    def dashboard():
        user_role = session.get('role')
        conn = database.get_db_connection()
        cursor = conn.cursor()
        if user_role == 'admin':
            cursor.execute('SELECT * FROM documents ORDER BY upload_date DESC')
        else:
            cursor.execute('SELECT * FROM documents WHERE category = ? ORDER BY upload_date DESC', (user_role,))
        documents = cursor.fetchall()
        conn.close()
        return render_template('dashboard.html', documents=documents, role=user_role, username=session.get('username'))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)