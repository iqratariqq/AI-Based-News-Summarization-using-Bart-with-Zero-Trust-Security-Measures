from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import bcrypt
import logging
from urllib.parse import urlparse
from newspaper import Article, network
from transformers import BartForConditionalGeneration, BartTokenizer
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import random

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'secret123')

# Rate limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])
login_limiter = limiter.shared_limit("10 per 10 minutes", scope="login_attempt")

# Secure session config
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_valid_url(url):
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme.startswith('http') or not parsed_url.netloc:
            return False
        safe_domains = ['bbc.com', 'cnn.com', 'nytimes.com', 'reuters.com']
        return any(domain in parsed_url.netloc for domain in safe_domains)
    except Exception as e:
        logging.error(f"Error validating URL: {str(e)}")
        return False

def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f)

def generate_captcha():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    session['captcha_answer'] = str(a + b)
    return f"What is {a} + {b}?"

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        users = load_users()
        if username in users:
            logging.warning(f"Signup failed – User already exists: {username}")
            return "User already exists!"
        hashed_pw = bcrypt.hashpw(password, bcrypt.gensalt())
        users[username] = hashed_pw.decode('utf-8')
        save_users(users)
        logging.info(f"New user created: {username}")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
@login_limiter
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        users = load_users()
        failed_attempts = session.get('failed_logins', 0)

        captcha_required = failed_attempts >= 3

        # Agar user exist karta hai
        if username in users:
            hashed_pw = users[username].encode('utf-8')

            # Agar password sahi hai
            if bcrypt.checkpw(password, hashed_pw):
                if captcha_required:
                    user_captcha = request.form.get('captcha')
                    correct = session.get('captcha_answer')
                    if not user_captcha or user_captcha.strip() != correct:
                        logging.warning(f"CAPTCHA failed for: {username}")
                        return render_template('login.html', captcha=True, captcha_question=generate_captcha(), error="❌ Incorrect CAPTCHA!")

                # Password and CAPTCHA (if required) both correct
                session['username'] = username
                session['failed_logins'] = 0
                logging.info(f"Login successful: {username}")
                return redirect(url_for('index'))

            else:
                failed_attempts += 1
                session['failed_logins'] = failed_attempts
                logging.warning(f"Wrong password for user: {username}")

        else:
            failed_attempts += 1
            session['failed_logins'] = failed_attempts
            logging.warning(f"Login failed – user not found: {username}")

        return render_template('login.html', captcha=captcha_required, captcha_question=generate_captcha(), error="Invalid credentials!")

    return render_template('login.html', captcha=(session.get('failed_logins', 0) >= 3), captcha_question=generate_captcha())


@app.route('/logout')
def logout():
    username = session.get('username')
    session.clear()
    logging.info(f"User logged out: {username}")
    return redirect(url_for('login'))

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        logging.warning("Unauthorized access attempt to /index")
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('index.html', show_summary=False)

    elif request.method == 'POST':
        network.UserAgent = 'Mozilla/5.0'
        url = request.form['url']
        logging.info(f"User '{session['username']}' submitted URL: {url}")

        if not is_valid_url(url):
            logging.warning(f"Invalid or unsafe URL by user '{session['username']}': {url}")
            return render_template('index.html', error="⚠️ Invalid or unsafe link.", show_summary=False)

        try:
            article = Article(url)
            article.download()
            article.parse()
            text = article.text
            title = article.title

            model_name = './model'
            tokenizer = BartTokenizer.from_pretrained(model_name)
            model = BartForConditionalGeneration.from_pretrained(model_name)

            inputs = tokenizer.encode(text, return_tensors='pt', max_length=1024, truncation=True)
            summary_ids = model.generate(inputs, num_beams=4, max_length=150, early_stopping=True)
            summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

            logging.info(f"Summary generated for user '{session['username']}' – Title: {title}")
            return render_template('index.html', summary=summary, text=text, show_summary=True, title=title)

        except Exception as e:
            logging.error(f"Error summarizing article from URL '{url}': {str(e)}")
            return render_template('index.html', error=f"⚠️ Failed to summarize: {str(e)}", show_summary=False)

if __name__ == '__main__':
    app.run(debug=True)
