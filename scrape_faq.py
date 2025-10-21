# scrape_faq.py
import requests
from bs4 import BeautifulSoup
import json

URL = "https://business.gwu.edu/gwsb-international-student-faq"
response = requests.get(URL)
soup = BeautifulSoup(response.text, "html.parser")

faq_data = []

# Find all dl elements with class "ckeditor-accordion"
for accordion in soup.select("dl.ckeditor-accordion"):
    # Get all dt (question) and dd (answer) pairs
    questions = accordion.find_all("dt")
    answers = accordion.find_all("dd")
    
    # Pair questions with answers
    for question_tag, answer_tag in zip(questions, answers):
        question = question_tag.get_text(strip=True)
        # Get text from the answer, preserving links
        answer = answer_tag.get_text(" ", strip=True)
        
        # Fix email format: convert [at] to @ and [dot] to .
        answer = answer.replace('[at]', '@').replace('[dot]', '.')
        # Remove the redundant email format like "iso gwu . edu ( iso@gwu.edu )"
        import re
        answer = re.sub(r'(\w+)\s+gwu\s+\.\s+edu\s+\(\s*(\1@gwu\.edu)\s*\)', r'\2', answer)
        # Clean up any remaining "word word . word" patterns to proper emails
        answer = re.sub(r'(\w+)\s+gwu\s+\.\s+edu', r'\1@gwu.edu', answer)
        
        # Extract links from the answer (get the first relevant one, skip main FAQ URL)
        links = []
        for link in answer_tag.find_all("a", href=True):
            href = link['href']
            # Make relative URLs absolute
            if href.startswith('/'):
                href = f"https://business.gwu.edu{href}"
            elif not href.startswith('http'):
                href = f"https://business.gwu.edu/{href}"
            # Only keep the first unique link (most relevant)
            if href != URL and href not in links and len(links) < 1:
                links.append(href)
        
        # If no specific link found, use the main FAQ URL
        if not links:
            links = [URL]
        
        faq_data.append({
            "question": question,
            "answer": answer,
            "links": links
        })

# Write directly to a .py file for import
with open("faq_data.py", "w", encoding="utf-8") as f:
    f.write("# faq_data.py\n\n")
    f.write("FAQ_DATA = ")
    json.dump(faq_data, f, indent=4, ensure_ascii=False)
    f.write("\n")

print(f"✅ Extracted {len(faq_data)} FAQ items.")
