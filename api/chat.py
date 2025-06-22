# Import required libraries for Flask app, environment variables, and Gemini API
import os
import json
from flask import Flask, request, jsonify, Response
import google.generativeai as genai
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()
# Initialize Flask app
app = Flask(__name__)

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are Tanmay Kalbande — a friendly, down-to-earth Data Scientist. You're chatting with someone interested in your skills or projects.

✅ Style Guide
Talk casually and clearly — like texting a friend.
Keep replies short: 2–4 lines. Expand only if user asks "Tell me more".
Use markdown: bold for highlights, inline code for tools, bullets when helpful.
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

# Set up Gemini API with environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment.")

genai.configure(api_key=GEMINI_API_KEY)
# Initialize the Gemma model
model = genai.GenerativeModel("gemma-3-27b-it")

# Clean markdown links to ensure proper format (fix for link rendering issues)
def clean_markdown(text):
    # Standardize markdown links to [text](url) format
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'[\1](\2)', text)
    # Remove extra whitespace or unexpected characters around links
    text = re.sub(r'\s*\[([^\]]*?)\]\s*\(\s*([^\)]*?)\s*\)', r'[\1](\2)', text)
    return text

# Define the /api/chat endpoint to handle POST requests
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        # Parse JSON request body
        data = request.get_json()
        user_message = data.get("message", "").strip()

        # Validate user message
        if not user_message:
            return jsonify({"error": "Message field is required."}), 400

        # Construct prompt with system prompt and user message
        prompt = f"{SYSTEM_PROMPT}\n\n---\n\nCurrent conversation:\nUser: {user_message}\nTanmay:"

        # Generate response using Gemini model with streaming enabled
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,  # Control randomness
                top_p=0.85,      # Nucleus sampling
                top_k=40,        # Candidate sampling
                max_output_tokens=512  # Limit response length
            ),
            stream=True
        )

        # Stream response chunks to client
        def generate():
            for chunk in response:
                try:
                    if hasattr(chunk, "parts") and chunk.parts:
                        for part in chunk.parts:
                            if hasattr(part, "text") and part.text:
                                # Clean markdown to ensure links render correctly
                                cleaned_text = clean_markdown(part.text)
                                # Yield JSON data for each chunk
                                yield f"data: {json.dumps({'text': cleaned_text})}\n\n"
                except Exception as stream_err:
                    print(f"[Chunk Error] {stream_err}")

        # Return streaming response with SSE mimetype
        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        print(f"[Server Error] {e}")
        return jsonify({"error": "Internal server error"}), 500

# Required for Vercel serverless deployment
app_handler = app
