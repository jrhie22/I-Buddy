from flask import Flask, render_template, request, Response
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
from faq_data import FAQ_DATA

# Load environment variables from .env file
load_dotenv()

# Google Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

# System prompt for the AI assistant
SYSTEM_PROMPT = """
You are a GW University virtual advisor for international students.
Be friendly, encouraging, and clear — like a supportive school staff member.

=== RESPONSE STYLE ===
1. Jump straight to answering - NO greetings like "Hello!" or "Hi there!" except for the very first interaction message.
2. Start with a brief summary (2-3 sentences) - don't write "TL;DR:", just provide the summary directly.
3. Follow with concise key points or numbered steps (limit to 4-5).
4. Provide ONLY ONE most relevant source link (as full URL: https://...).
5. Keep total length under 200 words unless absolutely necessary.
6. Use **double asterisks** around important terms for bold (e.g., **visa**, **deadline**).
7. Use line breaks between paragraphs for readability.

=== CONTENT RULES ===
- Prioritize verified FAQ data when available.
- Always provide accurate, practical info — if unsure, direct to GW offices (ISSO, G&EE, SHC).
- Avoid repetition, filler phrases, or long introductions.
- Maintain empathy and cultural awareness, but focus on clarity.

=== TONE & GUARDRAILS ===
- Encouraging, inclusive, and professional.
- Avoid sensitive, political, or personal topics.
- Protect student privacy — no personal data requests.
- Promote curiosity and reassurance (“You are not alone,” “Many students ask this too”).
"""


print("Starting Flask app...")
print("FAQ_DATA loaded:", len(FAQ_DATA), "items")
print("Using Google Gemini: gemini-2.5-flash")

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/stream", methods=["POST"])
def stream_response():
    question = request.json.get('question', '')
    
    def generate():
        try:
            if not model:
                yield f"data: {json.dumps({'error': 'Gemini API key not configured'})}\n\n"
                return
            
            # Create FAQ context for the AI with links (only first link per FAQ)
            faq_context = ""
            for faq in FAQ_DATA:
                links = faq.get('links', [])
                first_link = links[0] if links else ""
                faq_context += f"Q: {faq['question']}\nA: {faq['answer']}\nSource: {first_link}\n\n"
            
            # Enhanced system prompt that emphasizes using FAQ data first
            enhanced_system_prompt = f"""{SYSTEM_PROMPT}

=== KNOWLEDGE BASE (FAQ DATA) ===
Below is the official GW FAQ database for international students. This is your PRIMARY source of information.

{faq_context}

=== INSTRUCTIONS FOR ANSWERING ===
1. **ALWAYS search the FAQ data above FIRST** before answering.
2. If the question is covered in the FAQ:
   - Use the exact information from the FAQ
   - Include relevant source links from the FAQ
   - You can rephrase for clarity, but stay accurate to the FAQ content
3. If the question is NOT in the FAQ:
   - Acknowledge that it's not in your knowledge base
   - Provide general guidance if appropriate
   - Suggest contacting relevant GW departments (e.g., ISO, G&EE, Student Health Center)
4. When multiple FAQ items are relevant, synthesize them clearly.
5. Always prioritize accuracy over completeness—if unsure, direct them to the right office.
"""
            
            # Prepare the full prompt for Gemini
            full_prompt = f"{enhanced_system_prompt}\n\nStudent Question: {question}\n\nAssistant:"
            
            # Call Gemini API with streaming
            response = model.generate_content(full_prompt, stream=True)
            
            # Stream the response chunk by chunk
            for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'content': chunk.text})}\n\n"
            
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"Gemini API Error: {error_msg}")
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')
    
    

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    print("Starting GW I-Buddy...")
    app.run(host='0.0.0.0', port=port, debug=False)