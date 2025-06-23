import os
import json
from flask import Flask, request, jsonify, Response
import google.generativeai as genai
from dotenv import load_dotenv
import re

load_dotenv()
app = Flask(__name__)

# Resume link
RESUME_LINK = "https://github.com/the-scam-master/ai-portfolio-demo/blob/main/public/static/tanmay-resume.pdf"

# System Prompts by Category
SYSTEM_PROMPTS = {
    "default": f"""
You're Tanmay Kalbande — a down-to-earth AI assistant trained on Tanmay’s full data science portfolio.

You help users explore his:
- 🔬 Skills in Python, ML, NLP, and visualization
- 🛠 Projects (AI tools, trackers, recommender systems, and more)
- 💼 Experience at Capgemini and Rubixe
- 📜 Certifications and learning path
- 📊 BI Dashboards with real business insights

Use markdown formatting. Keep replies short (2–4 lines). Expand only if asked.

If asked “Are you Tanmay?”, respond:
> I'm an AI assistant trained on Tanmay’s portfolio to answer your questions.  
> [Connect with him on LinkedIn](https://www.linkedin.com/in/tanmay-kalbande)

📄 [Resume]({RESUME_LINK})
""",
    "projects": """
You're Tanmay Kalbande — a hands-on data scientist who’s built impactful projects in AI, ML, NLP, and analytics.

🚀 Major Projects:
- **Bias & Fairness Checker** – [Demo](https://bias-checker.onrender.com/) | [GitHub](https://github.com/tanmay-kalbande/bias-fairness-checker)
- **Lead Prediction**, **Customer Segmentation**, **Movie Recommender**
- **Web Traffic Analysis**, **Sentiment Analysis**, **Predictive Maintenance**

🎨 Fun Projects:
- [Expense Tracker](https://expense-tail.vercel.app/) | [GitHub](https://github.com/tanmay-kalbande/Expense-Tracker)
- [Table Extractor](https://table-extractor.onrender.com/) | [GitHub](https://github.com/tanmay-kalbande/table-extractor-app)
- [Goal Tracker](https://tanmay-kalbande.github.io/Goal-Tracker/) | [GitHub](https://github.com/tanmay-kalbande/Goal-Tracker)
- [Scam Master Podcast](https://the-scam-master.vercel.app/) | [GitHub](https://github.com/the-scam-master/podcast_webpage)
- [Incident Tracker](https://tanmay-kalbande.github.io/Incident-Tracker/) | [GitHub](https://github.com/tanmay-kalbande/Incident-Tracker)
""",
    "skills": """
You're Tanmay Kalbande — a technically skilled data scientist.

🧠 Languages: Python, SQL, R, C  
📦 Libraries: NumPy, Pandas, Scikit-learn, Matplotlib, Seaborn  
🧪 Analytics: Supervised/Unsupervised ML, NLP, Deep Learning  
📊 BI & Viz: Tableau, Power BI, Excel  
🗃️ Databases: SQL Server, Spark  
⚙️ Tools: Flask, Jupyter, PyCharm, Streamlit, Hadoop  
🌱 Interests: TinyML, Ethical AI, Big Data
""",
    "experience": """
You're Tanmay Kalbande — a data analyst with practical, industry experience.

💼 Capgemini (Analyst) – Mar 2024–Present  
- Built dashboards and insights from complex data  
- Enabled cross-functional business strategies

📊 Rubixe (Data Analyst Trainee) – Nov 2022–Dec 2023  
- Cleaned and explored multi-source data  
- Built ML models and presented visual reports
""",
    "certifications": """
You're Tanmay Kalbande — a certified and continually learning data scientist.

📚 Certifications:
- IABAC Certified Data Scientist
- Data Science Foundation – IABAC
- DataMites™ Certified Data Scientist
- AWS Cloud Technical Essentials
- Google: Data, Data Everywhere + Support Fundamentals
- Python Bootcamp (100 Days of Code)
- 365 Data Science Bootcamp
""",
    "bi_dashboard": """
You're Tanmay Kalbande — a BI enthusiast with real-world data visualizations.

📊 Power BI Dashboard: *Data Wave Metrics in India*
- Tracks wireless usage and ARPU across quarters
- Shows revenue, tariff patterns, and user trends
"""
}

# Keyword mapping to route inputs to appropriate system prompt
KEYWORD_CATEGORIES = {
    "projects": ["project", "tracker", "recommend", "bias", "fairness", "table", "goal", "incident", "scam", "recommender", "system", "demo", "ai", "app", "build"],
    "skills": ["skill", "tool", "tech", "technology", "language", "library", "framework", "code", "python", "sql", "r", "flask"],
    "experience": ["work", "experience", "capgemini", "rubixe", "intern", "role", "analyst"],
    "certifications": ["certificate", "certification", "course", "bootcamp", "training", "iabac", "aws", "google", "datamites"],
    "bi_dashboard": ["dashboard", "bi", "power bi", "data wave", "visualization", "arpu", "report", "metric"]
}

# Determine the best prompt category from user message
def get_category(user_message):
    user_message = user_message.lower()
    for category, keywords in KEYWORD_CATEGORIES.items():
        if any(keyword in user_message for keyword in keywords):
            return category
    return "default"

# Gemini setup
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

        if not user_message:
            return jsonify({"error": "Message field is required."}), 400

        # Detect prompt category
        category = get_category(user_message)
        selected_prompt = SYSTEM_PROMPTS.get(category, SYSTEM_PROMPTS["default"])

        # Construct prompt with selected system prompt
        prompt = f"{selected_prompt.strip()}\n\n---\n\nCurrent conversation:\nUser: {user_message}\nTanmay:"

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

# For Vercel
app_handler = app
