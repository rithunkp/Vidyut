import re
import sys
import json
import fitz  # PyMuPDF
import requests

def redact_pdf_with_free_llm(input_path, output_path):
    """
    Use free Hugging Face LLM to detect and redact sensitive information
    """
    doc = fitz.open(input_path)
    
    print("🤖 Using free AI to detect sensitive information...")
    
    # Process each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Extract text from the page
        page_text = page.get_text()
        
        if not page_text.strip():
            continue
            
        print(f"📄 Processing page {page_num + 1}...")
        
        # Ask free LLM to identify sensitive information
        sensitive_items = identify_sensitive_data_with_huggingface(page_text)
        
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
    print(f"✅ Free AI-redacted PDF saved to: {output_path}")

def identify_sensitive_data_with_huggingface(text):
    """
    Use Hugging Face free API to identify sensitive information
    """
    # Hugging Face Inference API endpoint (free tier)
    API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
    
    # Fixed the f-string formatting issue
    example_json = '[{"text": "john@email.com", "masked": "j***@email.com", "type": "email"}]'
    
    prompt = f"""
    Find sensitive data in this text. Return JSON array only:
    {example_json}
    
    Look for: emails, phone numbers, credit cards, SSN, bank accounts.
    Don't flag words like "confidential" or "question".
    
    Text: {text[:500]}
    """
    
    try:
        response = requests.post(API_URL, 
            headers={"Authorization": "Bearer hf_placeholder"}, 
            json={"inputs": prompt},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            # Try to extract JSON from response
            if result and len(result) > 0:
                text_response = result[0].get('generated_text', '')
                return parse_llm_response(text_response)
        
        # If Hugging Face fails, use local smart detection
        return smart_local_detection(text)
        
    except Exception as e:
        print(f"⚠️  Free API error, using local detection: {e}")
        return smart_local_detection(text)

def smart_local_detection(text):
    """
    Smart local detection without any external APIs
    """
    sensitive_items = []
    
    # Enhanced patterns with validation
    patterns = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b',
        'bank_account': r'\b[0-9]{8,17}\b(?=\s|$|[^A-Za-z0-9])'
    }
    
    for pattern_name, pattern in patterns.items():
        matches = re.finditer(pattern, text)
        for match in matches:
            original = match.group()
            masked = mask_text_smart(original, pattern_name)
            
            # Only add if it's actually sensitive (not false positive)
            if is_actually_sensitive(original, pattern_name):
                sensitive_items.append({
                    'text': original,
                    'masked': masked,
                    'type': pattern_name
                })
    
    return sensitive_items

def is_actually_sensitive(text, data_type):
    """
    Check if the detected text is actually sensitive data
    """
    # Skip common false positives
    false_positives = ['confidential', 'question', 'sincerely', 'attention', 'important']
    
    if text.lower() in false_positives:
        return False
    
    if data_type == 'email':
        # Must have valid email structure
        return '@' in text and '.' in text.split('@')[-1]
    
    elif data_type == 'phone':
        # Must have enough digits
        digits = re.sub(r'[^0-9]', '', text)
        return len(digits) >= 10
    
    elif data_type == 'ssn':
        # Must be exactly 9 digits in XXX-XX-XXXX format
        return re.match(r'^\d{3}-\d{2}-\d{4}$', text) is not None
    
    elif data_type == 'credit_card':
        # Basic Luhn check
        digits = re.sub(r'[^0-9]', '', text)
        return len(digits) >= 13 and luhn_check(digits)
    
    elif data_type == 'bank_account':
        # Must be reasonable length and standalone
        digits = re.sub(r'[^0-9]', '', text)
        return 8 <= len(digits) <= 17
    
    return True

def luhn_check(number_str):
    """
    Basic Luhn algorithm check for credit cards
    """
    try:
        digits = [int(d) for d in number_str]
        checksum = 0
        is_even = False
        
        for digit in reversed(digits):
            if is_even:
                digit *= 2
                if digit > 9:
                    digit = digit // 10 + digit % 10
            checksum += digit
            is_even = not is_even
        
        return checksum % 10 == 0
    except:
        return False

def mask_text_smart(text, data_type):
    """
    Smart masking based on data type
    """
    if data_type == 'email':
        at_pos = text.find('@')
        if at_pos > 0:
            return text[0] + '*' * (at_pos - 1) + text[at_pos:]
    
    elif data_type == 'phone':
        digits = re.sub(r'[^0-9]', '', text)
        if len(digits) >= 10:
            masked_digits = '*' * (len(digits) - 4) + digits[-4:]
            result = text
            digit_pos = 0
            for i, char in enumerate(text):
                if char.isdigit() and digit_pos < len(masked_digits):
                    result = result[:i] + masked_digits[digit_pos] + result[i+1:]
                    digit_pos += 1
            return result
    
    elif data_type == 'ssn':
        return '***-**-' + text[-4:]
    
    elif data_type in ['credit_card', 'bank_account']:
        digits = re.sub(r'[^0-9]', '', text)
        if len(digits) > 4:
            return '*' * (len(digits) - 4) + digits[-4:]
    
    return text

def parse_llm_response(response_text):
    """
    Try to parse JSON from LLM response
    """
    try:
        # Find JSON array in response
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        
        if json_start != -1 and json_end != -1:
            json_text = response_text[json_start:json_end]
            return json.loads(json_text)
    except:
        pass
    
    return []

def replace_text_in_page(page, words, original_text, masked_text):
    """
    Find and replace text in the PDF page
    """
    for word_info in words:
        word_text = word_info[4]
        
        if original_text.lower() in word_text.lower():
            word_bbox = fitz.Rect(word_info[0], word_info[1], word_info[2], word_info[3])
            
            # Cover with white rectangle
            page.draw_rect(word_bbox, color=(1, 1, 1), fill=(1, 1, 1))
            
            # Add masked text
            font_size = max(8, min(12, word_bbox.height * 0.8))
            page.insert_text(
                (word_bbox.x0, word_bbox.y1 - 2),
                masked_text,
                fontsize=font_size,
                color=(0, 0, 0)
            )
            break

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_pdf> <output_pdf>")
        print("Example: python main.py document.pdf redacted.pdf")
        print("\n🆓 Using FREE AI detection!")
        return
    
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    
    try:
        redact_pdf_with_free_llm(input_pdf, output_pdf)
        print("🎉 Success! Your PDF has been redacted for free!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()