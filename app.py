import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
import os

DEFAULT_DB_CONFIG = {
    "dbname": "library_db",
    "user": "postgres",
    "password": "secret",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection(config):
    return psycopg2.connect(**config, cursor_factory=RealDictCursor)

def init_db(config):
    conn = get_db_connection(config)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS authors (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            birth_year INT
        );
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            genre VARCHAR(100),
            year_published INT,
            author_id INT REFERENCES authors(id) ON DELETE SET NULL,
            created_by VARCHAR(255) NOT NULL
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def create_app(db_config=None):
    app = Flask(__name__)
    app.config['DB_CONFIG'] = db_config or DEFAULT_DB_CONFIG
    
    try:
        init_db(app.config['DB_CONFIG'])
    except Exception as e:
        print(f"DB Init skip: {e}")

    @app.route('/api/authors', methods=['POST'])
    def create_author():
        data = request.json
        if not data or 'name' not in data:
            return jsonify({"error": "name is required"}), 400
        conn = get_db_connection(app.config['DB_CONFIG'])
        cur = conn.cursor()
        cur.execute("INSERT INTO authors (name, birth_year) VALUES (%s, %s) RETURNING *",
                    (data['name'], data.get('birth_year')))
        new_author = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(new_author), 201

    @app.route('/api/authors', methods=['GET'])
    def get_authors():
        conn = get_db_connection(app.config['DB_CONFIG'])
        cur = conn.cursor()
        cur.execute("SELECT * FROM authors ORDER BY id")
        authors = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(authors), 200

    @app.route('/api/books', methods=['POST'])
    def create_book():
        data = request.json
        if not data or 'title' not in data or 'created_by' not in data:
            return jsonify({"error": "title and created_by are required"}), 400
        conn = get_db_connection(app.config['DB_CONFIG'])
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO books (title, genre, year_published, author_id, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING *",
            (data['title'], data.get('genre'), data.get('year_published'), data.get('author_id'), data['created_by'])
        )
        new_book = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(new_book), 201

    @app.route('/api/books', methods=['GET'])
    def get_books():
        conn = get_db_connection(app.config['DB_CONFIG'])
        cur = conn.cursor()
        cur.execute("SELECT * FROM books ORDER BY id")
        books = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(books), 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
