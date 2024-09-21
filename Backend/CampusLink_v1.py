from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",         
        user="root",              
        password="pr1y@nshuG",  
        database="forum"       
    )
    return connection

@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    username = data['username']
    email = data['email']

    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("INSERT INTO users (username, email) VALUES (%s, %s)", (username, email))
    connection.commit()

    user_id = cursor.lastrowid  
    cursor.close()
    connection.close()

    return jsonify({'message': 'User created', 'user_id': user_id})


@app.route('/user/<int:user_id>/tags', methods=['POST'])
def add_tags(user_id):
    tag_names = request.json.get('tags', [])

    connection = get_db_connection()
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

    return jsonify({'message': 'Tags added to user'})

# Route to get a user and their tags
@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    connection = get_db_connection()
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
    })

if __name__ == '__main__':
    app.run(debug=True)
