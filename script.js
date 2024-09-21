// Function to create a new post
function createPost() {
    const title = document.getElementById('postTitle').value;
    const content = document.getElementById('postContent').value;
    const userId = 1; // Replace with the actual user ID from JWT or session

    fetch('/posts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId, title: title, content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.post_id) {
            loadPosts(); // Reload posts after creating a new one
            document.getElementById('postTitle').value = '';
            document.getElementById('postContent').value = '';
        }
    });
}

// Function to load posts
function loadPosts() {
    fetch('/posts')
        .then(response => response.json())
        .then(data => {
            const postsDiv = document.getElementById('posts');
            postsDiv.innerHTML = ''; // Clear existing posts

            data.forEach(post => {
                const postDiv = document.createElement('div');
                postDiv.classList.add('post');
                postDiv.innerHTML = `
                    <h3>${post.title}</h3>
                    <p>${post.content}</p>
                    <p>Posted by: ${post.username} on ${new Date(post.created_at).toLocaleString()}</p>
                    <div class="reply">
                        <input type="text" placeholder="Reply..." />
                        <button onclick="replyToPost(${post.post_id}, this)">Reply</button>
                    </div>
                    <div id="replies-${post.post_id}"></div>
                `;
                postsDiv.appendChild(postDiv);
                loadReplies(post.post_id); // Load replies for each post
            });
        });
}

// Function to reply to a post
function replyToPost(postId, button) {
    const content = button.previousElementSibling.value;
    const userId = 1; // Replace with actual user ID

    fetch(`/posts/${postId}/replies`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId, content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.reply_id) {
            loadReplies(postId); // Reload replies after adding a new one
            button.previousElementSibling.value = ''; // Clear input
        }
    });
}

// Function to load replies for a post
function loadReplies(postId) {
    fetch(`/posts/${postId}/replies`)
        .then(response => response.json())
        .then(replies => {
            const repliesDiv = document.getElementById(`replies-${postId}`);
            repliesDiv.innerHTML = ''; // Clear existing replies

            replies.forEach(reply => {
                const replyDiv = document.createElement('div');
                replyDiv.innerHTML = `<strong>${reply.username}:</strong> ${reply.content} <em>on ${new Date(reply.created_at).toLocaleString()}</em>`;
                repliesDiv.appendChild(replyDiv);
            });
        });
}

// Load posts when the page is loaded
window.onload = loadPosts;
