# AI-Based-News-Summarization-using-Bart-with-Zero-Trust-Security-Measures
This is a Flask-based web application that summarizes news articles using the BART transformer model. It allows users to log in, enter a news article URL, and receive a summarized version of the article content.

---

## 🚀 Features

- 🔐 User Registration and Login System
- 🌐 URL input from trusted news websites
- 🧠 Text summarization using local BART model
- ⚠️ Error handling and session management
- 📄 HTML templates for login, signup, and results

---

## 🤖 Model Used

The summarization is powered by **BART (Bidirectional and Auto-Regressive Transformer)** — a transformer-based model trained for abstractive text summarization.

Model files required:
- `pytorch_model.bin`
- `config.json`
- `tokenizer.json`
- `vocab.json`
- `merges.txt`


  download these models manualy and Place all of them inside the `/model` directory.

---

## 📁 Project Structure
/project-root
│
├── app.py # Main Flask application
├── model/ # Contains BART model files
│ ├── config.json
│ ├── merges.txt
│ ├── pytorch_model.bin
│ ├── tokenizer.json
│ └── vocab.json
├── templates/ # HTML Templates
│ ├── login.html
│ ├── signup.html
│ └── index.html
├── users.json # User data storage
└── README.md # Project documentation
Set Up Virtual Environment

1.Set Up Virtual Environment
python -m venv venv
venv\Scripts\activate   # On Windows

2.Install Requirements
pip install -r requirements.txt

3.Download and Place Model Files
Place all BART model files inside the model/ folder.

4.Run the App
python app.py

Open your browser and visit: http://127.0.0.1:5000




