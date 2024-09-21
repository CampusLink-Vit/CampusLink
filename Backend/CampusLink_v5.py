from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import jwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace this with your own secret key
bcrypt = Bcrypt(app)
CORS(app)

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",         
        user="root",              
        password="pr1y@nshuG",  
        database="forum"       
    )
    return connection

# Route for user registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    email = data['email']
    password = data['password']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Check if the user already exists
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    if user:
        return jsonify({'message': 'User already exists'}), 400
    
    # Hash the password
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", 
                   (username, email, password_hash))
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({'message': 'User registered successfully'}), 201

# Route for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Fetch user details from the database
    cursor.execute("SELECT id, username, password_hash FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    user_id, username, password_hash = user
    
    # Check if the password is correct
    if not bcrypt.check_password_hash(password_hash, password):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Generate JWT token
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({'token': token, 'username': username}), 200

# Protected route (example)
@app.route('/profile', methods=['GET'])
def profile():
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'message': 'Token is missing'}), 401
    
    try:
        # Decode the JWT token
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = data['user_id']
    except:
        return jsonify({'message': 'Token is invalid or expired'}), 401
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Fetch user details
    cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if user is None:
        return jsonify({'message': 'User not found'}), 404
    
    username, email = user
    return jsonify({'username': username, 'email': email}), 200

# Test route
@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Test successful'})

# Route for creating a user
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

# Route to add tags to a user
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

# Route to add a post
@app.route('/posts', methods=['POST'])
def create_post():
    data = request.json
    user_id = data['user_id']
    title = data['title']
    content = data['content']

    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("INSERT INTO posts (user_id, title, content) VALUES (%s, %s, %s)", (user_id, title, content))
    connection.commit()

    post_id = cursor.lastrowid  
    cursor.close()
    connection.close()

    return jsonify({'message': 'Post created', 'post_id': post_id}), 201

# Route to fetch all posts
@app.route('/posts', methods=['GET'])
def get_posts():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT p.id, p.title, p.content, u.username, p.created_at FROM posts p JOIN users u ON p.user_id = u.id")
    posts = cursor.fetchall()

    posts_list = []
    for post in posts:
        posts_list.append({
            'post_id': post[0],
            'title': post[1],
            'content': post[2],
            'username': post[3],
            'created_at': post[4]
        })

    cursor.close()
    connection.close()

    return jsonify(posts_list)

# Route to add a reply to a post
@app.route('/posts/<int:post_id>/replies', methods=['POST'])
def add_reply(post_id):
    data = request.json
    user_id = data['user_id']
    content = data['content']

    connection = get_db_connection()
    cursor = connection.cursor()

    # Check if the post exists
    cursor.execute("SELECT id FROM posts WHERE id = %s", (post_id,))
    if cursor.fetchone() is None:
        return jsonify({'message': 'Post not found'}), 404

    cursor.execute("INSERT INTO replies (post_id, user_id, content) VALUES (%s, %s, %s)", (post_id, user_id, content))
    connection.commit()

    reply_id = cursor.lastrowid
    cursor.close()
    connection.close()

    return jsonify({'message': 'Reply added', 'reply_id': reply_id}), 201

# Route to fetch all replies for a post
@app.route('/posts/<int:post_id>/replies', methods=['GET'])
def get_replies(post_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Fetch the post
    cursor.execute("SELECT id FROM posts WHERE id = %s", (post_id,))
    if cursor.fetchone() is None:
        return jsonify({'message': 'Post not found'}), 404

    # Fetch all replies
    cursor.execute("""
        SELECT r.content, u.username, r.created_at
        FROM replies r JOIN users u ON r.user_id = u.id
        WHERE r.post_id = %s
    """, (post_id,))
    replies = cursor.fetchall()

    replies_list = []
    for reply in replies:
        replies_list.append({
            'content': reply[0],
            'username': reply[1],
            'created_at': reply[2]
        })

    cursor.close()
    connection.close()

    return jsonify(replies_list)

@app.route('/submit_query', methods=['POST'])
def submit_query():
    query = request.form.get('query')
    # Handle saving the query (to a database, etc.)
    return redirect('/query_page')  # Redirect back to the query page


if __name__ == '__main__':
    app.run(port=5004, debug=True)
