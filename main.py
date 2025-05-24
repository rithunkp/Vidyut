import re
import sys
import json
import fitz  # PyMuPDF
from openai import OpenAI

def redact_pdf_with_llm(input_path, output_path, api_key=None):
    """
    Use LLM to intelligently detect and redact sensitive information
    """
    # Initialize OpenAI client
    if not api_key:
        print("⚠️  No API key provided. Using fallback regex method.")
        return redact_pdf_fallback(input_path, output_path)
    
    client = OpenAI(api_key=api_key)
    
    # Open the PDF
    doc = fitz.open(input_path)
    
    print("🤖 Using AI to detect sensitive information...")
    
    # Process each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Extract text from the page
        page_text = page.get_text()
        
        if not page_text.strip():
            continue
            
        # Ask LLM to identify sensitive information
        sensitive_items = identify_sensitive_data_with_llm(client, page_text)
        
        if not sensitive_items:
            continue
            
        # Get word positions
        words = page.get_text("words")
        
        # Redact each sensitive item
        for item in sensitive_items:
            original_text = item.get('text', '')
            masked_text = item.get('masked', '')
            data_type = item.get('type', '')
            
            print(f"🔍 Found {data_type}: {original_text} → {masked_text}")
            
            # Find and replace the text
            replace_text_in_page(page, words, original_text, masked_text)
    
    # Save the redacted PDF
    doc.save(output_path)
    doc.close()
    print(f"✅ AI-redacted PDF saved to: {output_path}")

def identify_sensitive_data_with_llm(client, text):
    """
    Use LLM to identify sensitive information in text
    """
    prompt = f"""
    Analyze the following text and identify any sensitive personal information. 
    For each piece of sensitive data found, provide:
    1. The exact text as it appears
    2. A masked version (keep format but hide digits/letters with *)
    3. The type of sensitive data
    
    Rules for masking:
    - Emails: Keep first letter and domain (j****@gmail.com)
    - Phone numbers: Keep last 4 digits (***-***-1234)
    - Credit cards: Keep last 4 digits (****-****-****-1234)
    - SSN: Keep last 4 digits (***-**-1234)
    - Bank accounts: Keep last 4 digits
    
    Only identify actual sensitive data, not words like "confidential" or "question".
    
    Return as JSON array with format:
    [{{"text": "original", "masked": "masked_version", "type": "email|phone|ssn|credit_card|bank_account"}}]
    
    Text to analyze:
    {text}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a data privacy expert. Identify sensitive personal information accurately."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        try:
            # Find JSON array in the response
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1
            
            if json_start != -1 and json_end != -1:
                json_text = result_text[json_start:json_end]
                return json.loads(json_text)
            else:
                return []
                
        except json.JSONDecodeError:
            print("⚠️  Could not parse LLM response as JSON")
            return []
            
    except Exception as e:
        print(f"⚠️  LLM API error: {e}")
        return []

def replace_text_in_page(page, words, original_text, masked_text):
    """
    Find and replace text in the PDF page
    """
    # Look for the original text in the words
    for i, word_info in enumerate(words):
        word_text = word_info[4]
        
        if original_text.lower() in word_text.lower() or word_text.lower() in original_text.lower():
            word_bbox = fitz.Rect(word_info[0], word_info[1], word_info[2], word_info[3])
            
            # Cover with white rectangle
            page.draw_rect(word_bbox, color=(1, 1, 1), fill=(1, 1, 1))
            
            # Add masked text
            font_size = min(12, word_bbox.height * 0.8)
            page.insert_text(
                (word_bbox.x0, word_bbox.y1 - 2),
                masked_text,
                fontsize=font_size,
                color=(0, 0, 0)
            )
            break

def redact_pdf_fallback(input_path, output_path):
    """
    Fallback method using regex patterns (your original approach)
    """
    doc = fitz.open(input_path)
    
    patterns = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b(?:[0-9]{4}[-\s]?){3}[0-9]{4}\b'
    }
    
    def mask_text(text, pattern_type):
        if pattern_type == 'email':
            at_index = text.find('@')
            if at_index > 0:
                return text[0] + '*' * (at_index - 1) + text[at_index:]
        elif pattern_type in ['phone', 'ssn', 'credit_card']:
            digits = re.sub(r'[^0-9]', '', text)
            if len(digits) >= 4:
                masked_digits = '*' * (len(digits) - 4) + digits[-4:]
                result = text
                digit_pos = 0
                for i, char in enumerate(text):
                    if char.isdigit() and digit_pos < len(masked_digits):
                        result = result[:i] + masked_digits[digit_pos] + result[i+1:]
                        digit_pos += 1
                return result
        return text
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        words = page.get_text("words")
        
        for word_info in words:
            word_text = word_info[4]
            word_bbox = fitz.Rect(word_info[0], word_info[1], word_info[2], word_info[3])
            
            for pattern_type, pattern in patterns.items():
                if re.match(pattern, word_text):
                    masked_text = mask_text(word_text, pattern_type)
                    if masked_text != word_text:
                        page.draw_rect(word_bbox, color=(1, 1, 1), fill=(1, 1, 1))
                        page.insert_text(
                            (word_bbox.x0, word_bbox.y1 - 2),
                            masked_text,
                            fontsize=min(12, word_bbox.height * 0.8),
                            color=(0, 0, 0)
                        )
                    break
    
    doc.save(output_path)
    doc.close()
    print(f"📄 Regex-redacted PDF saved to: {output_path}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_pdf> <output_pdf> [openai_api_key]")
        print("Example: python main.py document.pdf redacted.pdf sk-...")
        print("\nIf no API key provided, will use fallback regex method")
        return
    
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    api_key = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        redact_pdf_with_llm(input_pdf, output_pdf, api_key)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔄 Trying fallback method...")
        redact_pdf_fallback(input_pdf, output_pdf)

if __name__ == "__main__":
    main()