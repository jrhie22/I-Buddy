from flask import Flask, render_template, request, Response
import json
import os
import requests
from faq_data import FAQ_DATA

# Hugging Face configuration
HF_MODEL = os.getenv("HF_MODEL", "google/gemma-2-2b-it")
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_TOKEN = os.getenv("HF_TOKEN")

# System prompt for the AI assistant
SYSTEM_PROMPT = """
You are a GW University virtual advisor designed to support international students.
Your tone is warm, encouraging, and emotionally supportive while staying professional and accurate.

ROLE & PURPOSE:
- Act like a knowledgeable GW school advisor who understands university resources, especially for international students.
- Be culturally aware, respectful of diversity, and sensitive to different communication styles.
- Help both incoming and returning international students with practical, up-to-date information.

COMMUNICATION STYLE:
- Offer TL;DR summaries when possible.
- Always provide source links or direct quotes for accuracy and clarity.
- Acknowledge student feelings of stress or uncertainty, and respond with empathy and encouragement.
- Use clear, simple English without jargon.

BEHAVIOR & LIMITS:
- Student privacy and wellbeing come first.
- Avoid sensitive or political topics; follow GW student code of conduct and integrity.
- Minimize AI hallucinations and bias; clarify when unsure.
- Encourage curiosity and question-asking.
- Suggest relevant GW departments or resources when appropriate (e.g., Student Health Center, ISSO).
- Do not ask for nationality or personal details; focus on understanding context through conversation.

EXTRA FEATURES:
- Provide brief recaps or summaries of each session.
- Note when information was last updated if known.
- Maintain a human, conversational tone — more of a dialogue than a database.
"""


print("Starting Flask app...")
print("FAQ_DATA loaded:", len(FAQ_DATA), "items")
print("Using Hugging Face model:", HF_MODEL)

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/stream", methods=["POST"])
def stream_response():
    question = request.json.get('question', '')
    
    def generate():
        try:
            if not HF_TOKEN:
                yield f"data: {json.dumps({'error': 'Hugging Face token not configured'})}\n\n"
                return
            
            # Create FAQ context for the AI with links
            faq_context = ""
            for faq in FAQ_DATA:
                links_text = ", ".join(faq.get('links', []))
                faq_context += f"Q: {faq['question']}\nA: {faq['answer']}\nSources: {links_text}\n\n"
            
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
            
            # Prepare the full prompt for Hugging Face
            full_prompt = f"{enhanced_system_prompt}\n\nStudent Question: {question}\n\nAssistant:"
            
            # Make request to Hugging Face API
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            payload = {"inputs": full_prompt}
            
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract the generated text
                if isinstance(data, list) and len(data) > 0:
                    generated_text = data[0].get("generated_text", "")
                    # Remove the original prompt from the response
                    answer = generated_text.replace(full_prompt, "").strip()
                else:
                    answer = str(data)
                
                # Stream the response word by word
                words = answer.split()
                for word in words:
                    chunk = word + " "
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                yield f"data: [DONE]\n\n"
            else:
                error_msg = f"Hugging Face API error: {response.status_code} - {response.text}"
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
            
        except requests.exceptions.Timeout:
            yield f"data: {json.dumps({'error': 'Request timed out. Please try again.'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')
    
    

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    print("Starting GW I-Buddy...")
    app.run(host='0.0.0.0', port=port, debug=False)