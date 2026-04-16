import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
import os

DEFAULT_DB_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
    "database": os.environ.get("POSTGRES_DB", "library_test_db"), 
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "secret"),
}

def get_db_connection(config):
    conn_params = config.copy()
    if "database" in conn_params:
        conn_params["dbname"] = conn_params.pop("database")
    return psycopg2.connect(**conn_params, cursor_factory=RealDictCursor)



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

    @app.route('/api/authors/<int:author_id>', methods=['GET'])
    def get_author(author_id):
        conn = get_db_connection(app.config['DB_CONFIG'])
        cur = conn.cursor()
        cur.execute("SELECT * FROM authors WHERE id = %s", (author_id,))
        author = cur.fetchone()
        cur.close()
        conn.close()
        if author:
            return jsonify(author), 200
        return jsonify({"error": "Author not found"}), 404

    @app.route('/api/authors/<int:author_id>', methods=['DELETE'])
    def delete_author(author_id):
        conn = get_db_connection(app.config['DB_CONFIG'])
        cur = conn.cursor()
        cur.execute("SELECT * FROM authors WHERE id = %s", (author_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "Author not found"}), 404
        cur.execute("DELETE FROM authors WHERE id = %s", (author_id,))
        conn.commit()
        cur.close()
        conn.close()
        return '', 204

    @app.route('/api/authors/<int:author_id>/books', methods=['GET'])
    def get_author_books(author_id):
        conn = get_db_connection(app.config['DB_CONFIG'])
        cur = conn.cursor()
        cur.execute("SELECT id FROM authors WHERE id = %s", (author_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "Author not found"}), 404
        cur.execute("SELECT * FROM books WHERE author_id = %s", (author_id,))
        books = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(books), 200

    @app.route('/api/books', methods=['POST'])
    def create_book():
        data = request.json
        if not data or 'title' not in data or 'created_by' not in data:
            return jsonify({"error": "title and created_by are required"}), 400
        conn = get_db_connection(app.config['DB_CONFIG'])
        cur = conn.cursor()
        if data.get('author_id'):
            cur.execute("SELECT id FROM authors WHERE id = %s", (data['author_id'],))
            if not cur.fetchone():
                cur.close()
                conn.close()
                return jsonify({"error": "Author not found"}), 400
                
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
			
			genre = request.args.get('genre')
			author_id = request.args.get('author_id')
			search = request.args.get('q') or request.args.get('search')
			
			query = "SELECT * FROM books WHERE 1=1"
			params = []
			
			if genre:
				query += " AND genre = %s"
				params.append(genre)
			if author_id:
				query += " AND author_id = %s"
				params.append(author_id)
			if search:
				query += " AND title ILIKE %s"
				params.append(f"%{search}%")
				
			cur.execute(query + " ORDER BY id", tuple(params))
			books = cur.fetchall()
			cur.close()
			conn.close()
			return jsonify(books), 200

    @app.route('/api/books/<int:book_id>', methods=['GET'])
    def get_book(book_id):
        conn = get_db_connection(app.config['DB_CONFIG'])
        cur = conn.cursor()
        cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        book = cur.fetchone()
        cur.close()
        conn.close()
        if book:
            return jsonify(book), 200
        return jsonify({"error": "Book not found"}), 404

    @app.route('/api/books/<int:book_id>', methods=['DELETE'])
    def delete_book(book_id):
        conn = get_db_connection(app.config['DB_CONFIG'])
        cur = conn.cursor()
        cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()
        cur.close()
        conn.close()
        return '', 204

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
