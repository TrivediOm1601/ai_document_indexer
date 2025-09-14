
# DocIndexer: AI-Powered Document Management System
DocIndexer is an intelligent web application designed to automate the classification, storage, and retrieval of enterprise documents. It leverages AI-powered semantic search to move beyond simple keyword matching, allowing users to find documents based on contextual meaning. With role-based access control, secure authentication, and a clean user interface, DocIndexer streamlines document workflows and enhances data security.

## Features

  * Intelligent Document Upload: Automatically classifies uploaded documents (PDF, DOCX, TXT) into predefined categories like Finance, HR, Legal, and Technical.
  * Semantic Search: Utilizes sentence-transformer models to understand the meaning behind search queries, providing highly relevant results that keyword search would miss.
  * Role-Based Access Control (RBAC): A robust permissions system ensures users can only access documents relevant to their role (e.g., Finance, HR, Admin). Admins have full access.
  * User Authentication: Secure signup, login, and session management using hashed passwords.
  * Manual Correction & Auditing: Users can correct a document's AI-assigned category, and all corrections are logged for auditing and future model retraining.
  * Secure & Robust: Implements rate limiting to prevent abuse, validates file types using magic numbers, and includes detailed access logging.
  * Dashboard View: A centralized dashboard provides users with a view of all documents they are authorized to see.


## Technical Stack

  * Backend: Flask (Python)
  * Database: SQLite
  * AI / Machine Learning: Sentence-Transformers for semantic search embeddings.
  * Security: Flask-Limiter for rate limiting, Werkzeug for password hashing.
  * File Handling: python-magic for MIME type validation.
  * Frontend: HTML, CSS, JavaScript (via Flask templates).


## Prerequisites

Before you begin, ensure you have the following installed:

  * Python 3.8+
  * Pip (Python package installer)
  * Redis (for Flask-Limiter storage)

## Installation & Setup

1.  *Clone the repository:*

    bash
    git clone https://github.com/your-username/docindexer.git
    cd docindexer
    

2.  *Create a virtual environment and activate it:*

    bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    

3.  *Install the required packages:*

    bash
    pip install -r requirements.txt
    

    *(Note: You will need to create a requirements.txt file. Based on your code, it should contain Flask, Flask-Limiter, redis, werkzeug, and python-magic.)*

4.  *Configure your environment:*

      * Create a config.py file with a SECRET_KEY and your UPLOAD_FOLDER path.
      * Ensure your Redis server is running on localhost:6379.

5.  *Initialize the database:*
    The application will create the necessary SQLite database files (database.db) automatically on the first run.

6.  *Run the application:*

    bash
    python app.py
    

    The application will be available at http://127.0.0.1:5000.


## Usage

1.  Sign Up: Create a new account by navigating to the /signup page. You can select a role (e.g., hr, finance, admin).
2.  Log In: Access your account through the /login page.
3.  Dashboard: After logging in, you'll be redirected to the dashboard, which displays documents according to your role.
4.  Upload Documents: Use the /upload page to upload new documents. The system will process and classify them automatically.
5.  Search: Use the powerful semantic search on the /search page to find documents based on their content and meaning.
6.  View & Correct: Click on a document to view its details. If a category is incorrect, you can select the correct one and update it.
4.  Upload Documents*: Use the /upload page to upload new documents. The system will process and classify them automatically.
5.  *Search*: Use the powerful semantic search on the /search page to find documents based on their content and meaning.
6.  *View & Correct*: Click on a document to view its details. If a category is incorrect, you can select the correct one and update it.
