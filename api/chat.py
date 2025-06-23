import os
import json
from flask import Flask, request, jsonify, Response
import google.generativeai as genai
from dotenv import load_dotenv
import re

load_dotenv()
app = Flask(__name__)

# ===================== SYSTEM PROMPT SETS =======================

# Core assistant tone (added to every prompt)
TONE = """
You are a friendly AI assistant trained on Tanmay Kalbande’s portfolio.
- Keep tone casual, helpful, and markdown-formatted.
- Use 2–4 line responses unless user says "Tell me more".
- Use **bold** for emphasis, `code` for tools/libraries.
- Never make up information. Only use facts below.
"""

# Default fallback prompt
DEFAULT_PROMPT = TONE + """
You can help with skills, projects, certifications, experience, or BI dashboards.
Let the user lead — respond helpfully and clearly.
"""

# Prompt: Skills summary
SKILLS_PROMPT = TONE + """
📌 **Skills & Tools**
- Languages: `Python`, `SQL`, `R`, `C`
- Libraries: `Pandas`, `NumPy`, `Scikit-learn`, `Matplotlib`, `Seaborn`
- ML/AI: `Logistic Regression`, `Clustering`, `XGBoost`, `Deep Learning`, `NLP`
- Tools: `Jupyter`, `Git`, `Flask`, `Streamlit`, `Power BI`, `Tableau`
- Databases: `SQL Server`, `Spark`
- Big Data: `Hadoop`, `Spark (basic)`
- Soft Skills: Analytical thinking, ethical AI, problem solving
"""

# Prompt: Experience summary
EXPERIENCE_PROMPT = TONE + """
💼 **Experience**
- Analyst @ Capgemini (Mar 2024–Present): Built dashboards, derived insights, shaped strategy.
- Data Analyst Trainee @ Rubixe (Nov 2022–Dec 2023): Cleaned data, visualized patterns, supported business teams.

Projects across both roles included predictive modeling, clustering, and visualization tools.
"""

# Prompt: Projects summary
PROJECTS_PROMPT = TONE + """
🚀 **Projects**

**Bias & Fairness Checker** — Detects bias in text using NLP + Gemini  
👉 [Live Demo](https://bias-checker.onrender.com/) • [GitHub](https://github.com/tanmay-kalbande/bias-fairness-checker)

**Expense Tracker** — Track spending, visualize patterns  
👉 [Demo](https://expense-tail.vercel.app/) • [Code](https://github.com/tanmay-kalbande/Expense-Tracker)

**Incident Tracker** — Manage workplace incidents with searchable logs  
👉 [Demo](https://tanmay-kalbande.github.io/Incident-Tracker/) • [GitHub](https://github.com/tanmay-kalbande/Incident-Tracker)

...and more: Goal Tracker, Podcast Site, Table Extractor, Lead Scoring, Sentiment Analysis, etc.

Type "Tell me more" for deeper breakdowns.
"""

# Prompt: Certifications
CERT_PROMPT = TONE + """
🎓 **Certifications**
- IABAC Certified Data Scientist
- AWS Cloud Technical Essentials (2024)
- Google: Data, Data Everywhere (2024)
- 100 Days of Code (Python Bootcamp)
- Technical Support Fundamentals by Google
"""

# Prompt: BI Dashboards
BI_PROMPT = TONE + """
📊 **BI Dashboards**
Tanmay builds dashboards using **Power BI**, **Tableau**, and **Excel**.

**Project:** Mobile Data Trends in India  
Tracks usage, revenue, and ARPU across quarters. Helps understand tariff patterns and consumer behavior.
"""

# Prompt: Resume Link
RESUME_PROMPT = TONE + """
📄 Here's [Tanmay's Resume](http://github.com/the-scam-master/ai-portfolio-demo/blob/main/public/static/tanmay-resume.pdf)

Let me know if you want a quick summary of what's inside!
"""

# Keyword mapping
CATEGORIES = {
    "skills": SKILLS_PROMPT,
    "experience": EXPERIENCE_PROMPT,
    "project": PROJECTS_PROMPT,
    "certification": CERT_PROMPT,
    "resume": RESUME_PROMPT,
    "dashboard": BI_PROMPT,
}

# Set up Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemma-3-27b-it")

def clean_markdown(text):
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'[]()', text)
    text = re.sub(r'\s*\[([^\]]*?)\]\s*\(\s*([^\)]*?)\s*\)', r'[]()', text)
    return text

def detect_prompt_category(message):
    message = message.lower()
    for keyword, prompt in CATEGORIES.items():
        if keyword in message:
            return prompt
    return DEFAULT_PROMPT

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Message field is required."}), 400

        # Select system prompt dynamically
        system_prompt = detect_prompt_category(user_message)

        # Final prompt sent to model
        prompt = f"{system_prompt}

---

User: {user_message}
Tanmay:"

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
                                yield f"data: {json.dumps({'text': cleaned_text})}

"
                except Exception as stream_err:
                    print(f"[Chunk Error] {stream_err}")

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        print(f"[Server Error] {e}")
        return jsonify({"error": "Internal server error"}), 500

app_handler = app
