import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, render_template, request, redirect, session, url_for
from transformers import pipeline
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit
import tensorflow as tf
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('request_data')
def handle_request_data():
    # Example: Generate random data for the graph
    data = {"x": random.randint(0, 100), "y": random.randint(0, 100)}
    emit('update_graph', data)

# MongoDB setup (replace 'mongodb://localhost:27017' with your MongoDB connection string)
client = MongoClient('mongodb+srv://kabi123:kabi123@cluster0.bunvu.mongodb.net/')
db = client['business_operations_db']
users_collection = db['users']

# Verify TensorFlow installation
print("TensorFlow Version:", tf.__version__)

# Initialize Hugging Face pipeline
generator = pipeline("text-generation", model="gpt2")

def get_huggingface_response(prompt):
    response = generator(prompt, max_length=100, num_return_sequences=1)
    return response[0]["generated_text"]

def generate_graph():
    # Example: Generate a random bar graph to display
    x = ['Category 1', 'Category 2', 'Category 3', 'Category 4']
    y = [random.randint(1, 10) for _ in x]
    
    plt.bar(x, y)
    plt.xlabel('Categories')
    plt.ylabel('Values')
    plt.title('Sample Graph')

    # Save the plot to a BytesIO object and convert to base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    
    return plot_url

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user already exists
        if users_collection.find_one({"username": username}):
            return "User already exists!"

        # Insert new user
        hashed_password = generate_password_hash(password)
        users_collection.insert_one({"username": username, "password": hashed_password})
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('assistant'))
        return "Invalid credentials"

    return render_template('login.html')

@app.route('/assistant', methods=['GET', 'POST'])
def assistant():
    if 'username' not in session:
        return redirect(url_for('login'))

    result = None
    graph_url = None
    
    if request.method == 'POST':
        operation = request.form['operation']
        input_text = request.form['input_text']
        
        # Map the operation to the corresponding prompt
        prompt_map = {
            "Business Analysis": f"Provide a detailed analysis for the following business challenge: {input_text}",
            "Market Insights": f"Provide market insights based on the following trend: {input_text}",
            "Financial Summary": f"Summarize the following financial data: {input_text}",
            "Customer Feedback": f"Analyze the following customer feedback: {input_text}"
        }

        if operation in prompt_map:
            result = get_huggingface_response(prompt_map[operation])
            # Generate a graph for the result
            graph_url = generate_graph()

    return render_template('assistant.html', result=result, graph_url=graph_url)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
