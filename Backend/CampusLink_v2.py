from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)

# Allow CORS from all origins for development/testing purposes
CORS(app, resources={r"/*": {"origins": "*"}})

# Function to establish a connection to the MySQL database
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",         
            user="root",              
            password="pr1y@nshuG",  
            database="forum"       
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Route to create a new user
@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')

    if not username or not email:
        return jsonify({'message': 'Missing username or email'}), 400

    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({'message': 'Database connection failed'}), 500

        cursor = connection.cursor()

        cursor.execute("INSERT INTO users (username, email) VALUES (%s, %s)", (username, email))
        connection.commit()

        user_id = cursor.lastrowid
        cursor.close()
        connection.close()

        return jsonify({'message': 'User created', 'user_id': user_id}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Route to add tags to a user
@app.route('/user/<int:user_id>/tags', methods=['POST'])
def add_tags(user_id):
    tag_names = request.json.get('tags', [])

    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({'message': 'Database connection failed'}), 500

        cursor = connection.cursor()

        # Check if the user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if cursor.fetchone() is None:
            return jsonify({'message': 'User not found'}), 404

        for tag_name in tag_names:
            # Check if the tag already exists
            cursor.execute("SELECT id FROM tags WHERE tag_name = %s", (tag_name,))
            tag = cursor.fetchone()

            if tag is None:
                # Insert the new tag
                cursor.execute("INSERT INTO tags (tag_name) VALUES (%s)", (tag_name,))
                tag_id = cursor.lastrowid
            else:
                tag_id = tag[0]

            # Insert into user_tags (using IGNORE to prevent duplicate entries)
            cursor.execute("INSERT IGNORE INTO user_tags (user_id, tag_id) VALUES (%s, %s)", (user_id, tag_id))

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'message': 'Tags added to user'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Route to get a user and their tags
@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({'message': 'Database connection failed'}), 500

        cursor = connection.cursor()

        # Fetch user details
        cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user is None:
            return jsonify({'message': 'User not found'}), 404

        username, email = user

        # Fetch user tags
        cursor.execute("""
            SELECT t.tag_name FROM tags t
            JOIN user_tags ut ON t.id = ut.tag_id
            WHERE ut.user_id = %s
        """, (user_id,))
        tags = [tag[0] for tag in cursor.fetchall()]

        cursor.close()
        connection.close()

        return jsonify({
            'username': username,
            'email': email,
            'tags': tags
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
