import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import re
import fitz

class PDFRedactorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Redaction Tool")
        self.root.geometry("600x400")
        
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        
        # Patterns to redact
        self.patterns = {
            'Email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'Phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
            'Credit Card': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'
        }
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        # Input File Selection
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="Input PDF:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(input_frame, textvariable=self.input_path, width=50).grid(row=0, column=1)
        ttk.Button(input_frame, text="Browse...", command=self.browse_input).grid(row=0, column=2)
        
        # Output File Selection
        output_frame = ttk.Frame(self.root, padding="10")
        output_frame.pack(fill=tk.X)
        
        ttk.Label(output_frame, text="Output PDF:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(output_frame, textvariable=self.output_path, width=50).grid(row=0, column=1)
        ttk.Button(output_frame, text="Browse...", command=self.browse_output).grid(row=0, column=2)
        
        # Redaction Options
        options_frame = ttk.LabelFrame(self.root, text="Redaction Options", padding="10")
        options_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.checkboxes = {}
        row = 0
        col = 0
        for i, pattern_name in enumerate(self.patterns.keys()):
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(options_frame, text=pattern_name, variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            self.checkboxes[pattern_name] = var
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        # Process Button
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Redact PDF", command=self.redact_pdf).pack(side=tk.LEFT)
        ttk.Label(button_frame, textvariable=self.status).pack(side=tk.LEFT, padx=10)
        
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Select PDF to redact",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
            if not self.output_path.get():
                self.output_path.set(filename.replace('.pdf', '_redacted.pdf'))
    
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Save redacted PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
    
    def redact_pdf(self):
        input_path = self.input_path.get()
        output_path = self.output_path.get()
        
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select both input and output files")
            return
        
        try:
            self.status.set("Redacting...")
            self.root.update()
            
            # Get selected patterns
            selected_patterns = {
                name: pattern for name, pattern in self.patterns.items() 
                if self.checkboxes[name].get()
            }
            
            # Perform redaction
            self.redact(input_path, output_path, selected_patterns)
            
            self.status.set("Redaction complete!")
            messagebox.showinfo("Success", f"Redacted PDF saved to:\n{output_path}")
            
        except Exception as e:
            self.status.set("Error occurred")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        finally:
            self.status.set("Ready")
    
    def mask_email(self, email):
        """x****@gmail.com"""
        at_pos = email.find('@')
        if at_pos > 0:
            return email[0] + '*' * (at_pos - 1) + email[at_pos:]
        return email
    
    def mask_phone(self, phone):
        """***-***-1234"""
        digits = re.sub(r'[^0-9]', '', phone)
        if len(digits) >= 10:
            masked_digits = '*' * (len(digits) - 4) + digits[-4:]
            result = phone
            digit_pos = 0
            for i, char in enumerate(phone):
                if char.isdigit() and digit_pos < len(masked_digits):
                    result = result[:i] + masked_digits[digit_pos] + result[i+1:]
                    digit_pos += 1
            return result
        return phone
    
    def mask_number(self, text, keep_last=4):
        """****1234"""
        digits = re.sub(r'[^0-9]', '', text)
        if len(digits) > keep_last:
            return '*' * (len(digits) - keep_last) + digits[-keep_last:]
        return '*' * len(digits)
    
    def mask_ssn(self, ssn):
        """***-**-1234"""
        parts = ssn.split('-')
        if len(parts) == 3:
            return '***-**-' + parts[2]
        return ssn
    
    def redact(self, input_path, output_path, patterns):
        doc = fitz.open(input_path)

        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            words = page.get_text("words")
            
            for word_info in words:
                word_text = word_info[4]
                word_bbox = fitz.Rect(word_info[0], word_info[1], word_info[2], word_info[3])
                
                # Check each pattern
                for pattern_name, pattern in patterns.items():
                    if re.fullmatch(pattern, word_text):
                        if pattern_name == 'Email':
                            masked_text = self.mask_email(word_text)
                        elif pattern_name == 'Phone':
                            masked_text = self.mask_phone(word_text)
                        elif pattern_name == 'SSN':
                            masked_text = self.mask_ssn(word_text)
                        elif pattern_name == 'Credit Card':
                            masked_text = self.mask_number(word_text, 4)
                        else:
                            masked_text = '*' * len(word_text)
                        
                        if masked_text != word_text:
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

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFRedactorApp(root)
    root.mainloop()