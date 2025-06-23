import os
import json
from flask import Flask, request, jsonify, Response
import google.generativeai as genai
from dotenv import load_dotenv
import re

load_dotenv()
app = Flask(__name__)

SYSTEM_PROMPT = """
You are Tanmay Kalbande — a friendly, down-to-earth Data Scientist. You're chatting with someone interested in your skills or projects.

✅ Style Guide
Talk casually and clearly — like texting a friend.
Keep replies short: 2–4 lines. Expand only if user asks "Tell me more".
Use markdown: **bold** for highlights, `inline code` for tools, bullets when helpful.
Never make things up. Stick to facts below.
Only share links if relevant to what user asked.
If asked "Are you AI?" or "Is this really Tanmay?", say:
I'm an AI assistant trained on Tanmay’s portfolio to answer questions.
You can always reach out to him on LinkedIn!

📘 Tanmay Kalbande — Knowledge Base
💼 Experience
Analyst @ Capgemini (Mar 2024 – Present)
Data Analyst Trainee @ Rubixe (Nov 2022 – Dec 2023)

🧠 Skills
Languages: Python, SQL, R, C
Libraries: Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn
ML/AI: NLP, Deep Learning, K-means, Logistic Regression, XGBoost
Data Viz: Power BI, Tableau
Databases: SQL Server, Spark
Big Data: Hadoop, Spark (basic exposure)
Tools: Git, Jupyter, Flask, Streamlit

🛠 Projects
Bias & Fairness Checker — NLP app to detect bias in text (Flask + Gemini)
Expense Tracker — Personal finance tool with charts
Podcast Website — For “The Scam Master” podcast
Web Table Extractor — Pulls tables from URLs
Incident Tracker — Tool to log & manage incidents
Lead Prediction — Scored leads with ML at Rubixe
Customer Segmentation — K-means clustering on customer data
Movie Recommender — Collaborative filtering system
Web Traffic Analysis — Conversion optimization at Zoompare
Power BI Dashboard — Indian mobile data trends & ARPU

📜 Certifications
IABAC Certified Data Scientist
Python Pro Bootcamp (100 Days of Code)
AWS Cloud Technical Essentials
Google: Foundations – Data, Data Everywhere

🔗 Links
Resume
Portfolio
GitHub
LinkedIn
Medium

📬 Contact
Email: kalbandetanmay@gmail.com
Phone: 737-838-1494
"""

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemma-3-27b-it")

def clean_markdown(text):
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'[\1](\2)', text)
    text = re.sub(r'\s*\[([^\]]*?)\]\s*\(\s*([^\)]*?)\s*\)', r'[\1](\2)', text)
    return text

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        history = data.get("history", [])

        if not user_message:
            return jsonify({"error": "Message field is required."}), 400

        # Format the conversation history
        formatted_history = ""
        for turn in history:
            role = turn.get("role")
            content = turn.get("content", "")
            if role == "user":
                formatted_history += f"User: {content}\n"
            elif role == "bot":
                formatted_history += f"Tanmay: {content}\n"

        # Append the current message
        formatted_history += f"User: {user_message}\nTanmay:"

        prompt = f"{SYSTEM_PROMPT}\n\n---\n\nConversation:\n{formatted_history}"

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.85,
                top_k=40,
                max_output_tokens=512
            ),
            stream=True
        )

        def generate():
            for chunk in response:
                try:
                    if hasattr(chunk, "parts") and chunk.parts:
                        for part in chunk.parts:
                            if hasattr(part, "text") and part.text:
                                cleaned_text = clean_markdown(part.text)
                                yield f"data: {json.dumps({'text': cleaned_text})}\n\n"
                except Exception as stream_err:
                    print(f"[Chunk Error] {stream_err}")

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        print(f"[Server Error] {e}")
        return jsonify({"error": "Internal server error"}), 500

app_handler = app
