import sys
import os
import PyPDF2
from openai import OpenAI
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QComboBox, QLineEdit, QGridLayout, QMessageBox
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

# Initialize and load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class PDFDropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setAcceptDrops(True)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Drag and drop a PDF file here.")
        self.text_edit.setReadOnly(True)
        
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("Enter target language (e.g., Spanish, German, etc.)")

        self.model_select = QComboBox()
        self.model_select.addItems(["gpt-3.5-turbo", "gpt-4o"])
        
        self.btn_translate = QPushButton("Translate Text")
        self.btn_translate.clicked.connect(self.prompt_for_translation)
        
        self.btn_open_file = QPushButton("Open Translated Text File")
        self.btn_open_file.clicked.connect(self.open_translated_file)
        self.btn_open_file.setEnabled(False)  # Disable until translation is done

        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)

        layout = QGridLayout()
        layout.addWidget(QLabel("PDF File:"), 0, 0)
        layout.addWidget(self.text_edit, 0, 1, 1, 2)
        layout.addWidget(QLabel("Language:"), 1, 0)
        layout.addWidget(self.language_input, 1, 1, 1, 2)
        layout.addWidget(QLabel("Model:"), 2, 0)
        layout.addWidget(self.model_select, 2, 1, 1, 2)
        layout.addWidget(self.btn_translate, 3, 2)
        layout.addWidget(self.btn_open_file, 3, 1)
        layout.addWidget(self.output_console, 4, 0, 1, 3)
        
        self.setLayout(layout)
        self.setWindowTitle('PDF Translator')
        self.resize(600, 400)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and len(urls) > 0:
            filepath = str(urls[0].toLocalFile())
            if filepath.lower().endswith('.pdf'):
                self.text_edit.setText(filepath)
                self.file_path = filepath
                event.accept()
            else:
                self.text_edit.setText("Please drop a PDF file.")
                event.ignore()

    def read_pdf(self, file_path):
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
        return text

    def calculate_cost(self, prompt_tokens, completion_tokens, model):
        if model == "gpt-3.5-turbo":
            input_cost = prompt_tokens * 0.50 / 1000000
            output_cost = completion_tokens * 1.50 / 1000000
        elif model == "gpt-4":
            input_cost = prompt_tokens * 5.00 / 1000000
            output_cost = completion_tokens * 15.00 / 1000000
        total_cost = input_cost + output_cost
        return input_cost, output_cost, total_cost

    def prompt_for_translation(self):
        if hasattr(self, 'file_path') and os.path.exists(self.file_path):
            text = self.read_pdf(self.file_path)
            model = self.model_select.currentText()
            target_language = self.language_input.text()
            
            estimated_prompt_tokens = len(text) / 4  # Simplified estimation
            estimated_completion_tokens = estimated_prompt_tokens * 0.9
            estimated_input_cost, estimated_output_cost, estimated_total_cost = self.calculate_cost(
                estimated_prompt_tokens, estimated_completion_tokens, model)

            self.output_console.append("Estimated tokens and costs:")
            self.output_console.append(f"Input Tokens: {estimated_prompt_tokens}, Output Tokens: {estimated_completion_tokens}")
            self.output_console.append(f"Estimated Cost: Input ${estimated_input_cost:.6f}, Output ${estimated_output_cost:.6f}, Total ${estimated_total_cost:.6f}")

            proceed = QMessageBox.question(self, "Confirm Translation", 
                                           "Proceed with translation? Check estimated costs in the console.",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if proceed == QMessageBox.Yes:
                self.translate_text(text, model, target_language)
        else:
            self.output_console.append("Please drop a valid PDF file first.")

    def translate_text(self, text, model, target_language):
        max_length = 5000
        translated_text = ''
        progress = 0
        for start in range(0, len(text), max_length):
            end = start + max_length
            chunk = text[start:end]
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": f"Translate the following text to {target_language}:\n\n{chunk}"}],
                max_tokens=4096
            )
            translated_text += response.choices[0].message.content.strip() + '\n\n'
            progress += end - start
            self.output_console.append(f"Progress: {progress}/{len(text)} chars translated")

        output_file = 'translated_text.txt'
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(translated_text)
        self.output_console.append("Translation complete! Output saved to 'translated_text.txt'")
        self.btn_open_file.setEnabled(True)
        self.text_edit.setPlaceholderText("Drag and drop a PDF file here.")
        self.text_edit.setText("")

    def open_translated_file(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath('translated_text.txt')))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = PDFDropWidget()
    mainWin.show()
    sys.exit(app.exec_())
