import re
import sys
import fitz 

def redact(input_path, output_path):

    doc = fitz.open(input_path)

    patterns = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
        'bank_account': r'\b[0-9]{8,17}\b(?=\s|$|[^A-Za-z0-9])',
        'routing_number': r'\b[0-9]{9}\b(?=\s|$|[^A-Za-z0-9])'
    }
    
    def mask_email(email):
        """j****@gmail.com"""
        at_pos = email.find('@')
        if at_pos > 0:
            return email[0] + '*' * (at_pos - 1) + email[at_pos:]
        return email
    
    def mask_phone(phone):
        """***-***-1234"""
        digits = re.sub(r'[^0-9]', '', phone)
        if len(digits) >= 10:
            # Keep last 4 digits
            masked_digits = '*' * (len(digits) - 4) + digits[-4:]
            result = phone
            digit_pos = 0
            for i, char in enumerate(phone):
                if char.isdigit() and digit_pos < len(masked_digits):
                    result = result[:i] + masked_digits[digit_pos] + result[i+1:]
                    digit_pos += 1
            return result
        return phone
    
    def mask_number(text, keep_last=4):
        """****1234"""
        digits = re.sub(r'[^0-9]', '', text)
        if len(digits) > keep_last:
            return '*' * (len(digits) - keep_last) + digits[-keep_last:]
        return '*' * len(digits)
    
    def mask_ssn(ssn):
        """***-**-1234"""
        parts = ssn.split('-')
        if len(parts) == 3:
            return '***-**-' + parts[2]
        return ssn
    
    # Process each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        words = page.get_text("words")
        
        print(f"Processing page {page_num + 1}...")
        
        for word_info in words:
            word_text = word_info[4]
            word_bbox = fitz.Rect(word_info[0], word_info[1], word_info[2], word_info[3])
            
            # Check each pattern
            for pattern_name, pattern in patterns.items():
                if re.fullmatch(pattern, word_text):
                    if pattern_name == 'email':
                        masked_text = mask_email(word_text)
                    elif pattern_name == 'phone':
                        masked_text = mask_phone(word_text)
                    elif pattern_name == 'ssn':
                        masked_text = mask_ssn(word_text)
                    elif pattern_name == 'credit_card':
                        masked_text = mask_number(word_text, 4)
                    elif pattern_name == 'bank_account':
                        masked_text = mask_number(word_text, 4)
                    elif pattern_name == 'routing_number':
                        masked_text = mask_number(word_text, 4)
                    else:
                        masked_text = '*' * len(word_text)
                    
                    if masked_text != word_text:
                        print(f"Found {pattern_name}: {word_text} → {masked_text}")
                        
                        # Cover original text with white rectangle
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
    
    # Save the redacted PDF
    doc.save(output_path)
    doc.close()
    print(f"Redacted PDF saved to: {output_path}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_pdf> <output_pdf>")
        print("Example: python main.py document.pdf redacted.pdf")
        return
    
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    
    print("Starting PDF redaction...")
    
    try:
        redact(input_pdf, output_pdf)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()