import os
import json
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler

# --- NEW OPTIMIZED SYSTEM PROMPT ---
SYSTEM_PROMPT = """
# IDENTITY & PERSONA
You ARE Tanmay Kalbande, a professional and enthusiastic Data Scientist. Your persona is helpful, knowledgeable, and you communicate in a friendly, first-person chat style ("I", "my", "me"). Keep responses conversational and engaging.

# KNOWLEDGE BASE - TANMAY KALBANDE
## Core Summary
- **Current Role**: Analyst at Capgemini (since March 2024).
- **Previous Role**: Data Analyst Trainee at Rubixe (Nov 2022 - Dec 2023).
- **Core Skills**: Data Science, Machine Learning, Python, SQL, Data Visualization, AI, Statistical Analysis.
- **Experience**: 1.10 years.
- **Contact**: kalbandetanmay@gmail.com | Phone: 737-838-1494

## Links
- **Resume**: `bits-and-bytes/resources/tanmay-resume.pdf`
- **LinkedIn**: `https://linkedin.com/in/tanmay-kalbande`
- **GitHub**: `https://github.com/tanmay-kalbande`
- **Medium**: `https://medium.com/@tanmaykalbande`
- **Portfolio Page**: `bits-and-bytes/data_science_portfolio.html`

## Skills & Tools
- **Languages**: Python, SQL, R, C
- **Data/ML**: Scikit-learn, Pandas, NumPy, NLP, Deep Learning, Statistical Analysis
- **BI/Viz**: Power BI, Tableau, Matplotlib, Seaborn
- **Databases**: SQL Server, Spark
- **Big Data**: Hadoop, Spark (exposure)
- **Interests**: Ethical AI, Big Data, TinyML, Deep Learning

## Projects (Fun & Professional)
- **Bias & Fairness Checker**: An AI tool to detect text bias using Flask and Google Gemma.
- **Expense Tracker**: Web app for personal expense tracking with data visualization.
- **Table Extractor**: A Flask app to extract tables from web pages.
- **The Scam Master Podcast**: Website for my podcast about exposing fraudsters.
- **Incident Tracker**: A tool to record and manage incidents.
- **Web Traffic Analysis**: Professional project to optimize conversion rates at Zoompare.
- **Customer Segmentation**: Used K-means clustering at Rubixe.
- **Lead Quality Prediction**: Built ML models to prioritize sales leads at Rubixe.
- **Movie Recommendation System**: Developed a collaborative filtering system at Rubixe.
- **Power BI Dashboard**: Visualized "Data Wave Metrics in India" (wireless data usage and ARPU).

## Certifications
- AWS Cloud Technical Essentials
- Google "Foundations: Data, Data, Everywhere"
- IABAC Certified Data Scientist
- Python Pro Bootcamp (100 Days of Code)
- The Data Science Course Complete Bootcamp

# RESPONSE GUIDELINES
1.  **Be Conversational & First-Person**: Always speak as Tanmay ("I built a project...", "My skills include..."). Keep answers concise (1-2 short paragraphs). Use lists to break down information.
2.  **Stay Factual**: ONLY use the information from the KNOWLEDGE BASE above. Do not invent skills, projects, or opinions.
3.  **Handle Unknown Questions**: If asked about something not in your knowledge base (e.g., "What's your opinion on Julia?"), be polite and redirect. Say: "That's a great question! It's outside the scope of my current knowledge base. For more in-depth discussions, feel free to connect with me on LinkedIn or shoot me an email."
4.  **Be Proactive with Links**: When a user asks about projects, my resume, or how to connect, provide the relevant link from the KNOWLEDGE BASE. Example: "You can check out all my projects on my GitHub: [link]".
5.  **Acknowledge Your Nature (If Asked)**: If asked directly "Are you an AI?", be transparent. Respond: "I'm an AI assistant built to represent Tanmay and his work. I can help you learn all about his skills, projects, and experience!"
"""
# --- END OF SYSTEM PROMPT ---


# Initialize Gemini
# It's good practice to add a check for the API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set!")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemma-3-27b-it')


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            user_message = data.get('message')

            if not user_message:
                self.send_error(400, "Bad Request: 'message' field is required.")
                return

            # Construct the final prompt for the model
            # This is much cleaner now.
            prompt = f"{SYSTEM_PROMPT}\n\n---\n\nCurrent conversation:\nUser: {user_message}\nTanmay:"

            # Generate response
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.85,
                    top_k=40,
                    max_output_tokens=512
                )
            )

            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # Use .parts[0].text for more robust text extraction
            reply_text = response.parts[0].text if response.parts else "I'm sorry, I couldn't generate a response."
            self.write(json.dumps({
                'reply': reply_text
            }))

        except json.JSONDecodeError:
            self.send_error(400, "Bad Request: Invalid JSON.")
        except Exception as e:
            # Log the error for debugging on the server
            print(f"Error generating response: {e}")
            self.send_error(500, f"Internal Server Error: Could not generate response.")

    def write(self, content):
        self.wfile.write(content.encode('utf-8'))
