import random
import string
import sqlite3
import re
import os
from flask import Flask, request, redirect

app = Flask(__name__)

# Connect to SQLite database (or create one if it doesn't exist)
DATABASE = 'url_shortener.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To access columns by name
    return conn

# Create table to store URLs if it doesn't exist
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS url_mapping (
            short_url TEXT PRIMARY KEY,
            original_url TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_table()  # Call function to create the table on startup

# Function to generate a random string for the short URL
def generate_short_url():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# Function to validate URL
def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

# Route to show a simple form to shorten URL
@app.route('/')
def index():
    return '''
        <form action="/shorten" method="POST">
            Enter URL: <input type="text" name="url">
            <input type="submit" value="Shorten">
        </form>
    '''

# Route to shorten the URL
@app.route('/shorten', methods=['POST'])
def shorten_url():
    original_url = request.form['url']

    # Validate URL
    if not is_valid_url(original_url):
        return "Invalid URL! Please enter a valid URL.", 400

    # Generate a short URL
    short_url = generate_short_url()

    # Insert the mapping into the SQLite database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO url_mapping (short_url, original_url) VALUES (?, ?)', (short_url, original_url))
    conn.commit()
    conn.close()

    # Display the shortened URL
    return f'Short URL is: <a href="{request.host_url}{short_url}">{request.host_url}{short_url}</a>'

# Redirect from short URL to the original URL
@app.route('/<short_url>')
def redirect_to_original(short_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT original_url FROM url_mapping WHERE short_url = ?', (short_url,))
    result = cursor.fetchone()
    conn.close()

    return redirect(result['original_url']) if result else 'URL not found', 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
