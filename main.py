import sys
import os
import PyPDF2
import ollama
import requests
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QLineEdit, QGridLayout, QMessageBox, QProgressBar
from PyQt5.QtCore import QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QDesktopServices

class TranslationWorker(QThread):
    progress_update = pyqtSignal(str, int)
    chunk_start = pyqtSignal(str)
    chunk_complete = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, text, model, target_language, file_path, max_length=5000):
        super().__init__()
        self.text = text
        self.model = model
        self.target_language = target_language
        self.file_path = file_path
        self.max_length = max_length
    
    def run(self):
        try:
            self.chunk_start.emit("Checking if Ollama is running...")
            try:
                health_response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if health_response.status_code != 200:
                    self.error.emit(f"Ollama health check failed. Status: {health_response.status_code}\nMake sure Ollama is running on http://localhost:11434")
                    return
                
                models_data = health_response.json()
                model_names = [model.get('name', '') for model in models_data.get('models', [])]
                if self.model not in model_names:
                    self.error.emit(f"Model '{self.model}' not found in Ollama.\nAvailable models: {', '.join(model_names) if model_names else 'none'}\n\nUse 'ollama pull {self.model}' to download the model.")
                    return
                    
            except requests.exceptions.Timeout:
                self.error.emit("Timeout connecting to Ollama. Make sure Ollama is running and responding.")
                return
            except requests.exceptions.ConnectionError:
                self.error.emit("Cannot connect to Ollama at http://localhost:11434\nMake sure Ollama is running.")
                return
            except requests.exceptions.RequestException as e:
                self.error.emit(f"Error checking Ollama: {str(e)}\nMake sure Ollama is running on http://localhost:11434")
                return
            except Exception as e:
                self.error.emit(f"Error verifying Ollama: {str(e)}")
                return
            
            self.chunk_complete.emit("Ollama connection verified, model found")
            
            self.chunk_start.emit("Testing model response (this may take a moment if model needs to load)...")
            try:
                test_payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": "Say 'test'"}],
                    "stream": False
                }
                test_response = requests.post(
                    "http://localhost:11434/api/chat",
                    json=test_payload,
                    timeout=(10, 300)
                )
                if test_response.status_code == 200:
                    response_data = test_response.json()
                    self.chunk_complete.emit("Model is ready and responding")
                else:
                    curl_cmd = f"curl http://localhost:11434/api/generate -d '{{\"model\":\"{self.model}\",\"prompt\":\"test\"}}'"
                    self.error.emit(f"Model test failed: Status {test_response.status_code}\nResponse: {test_response.text[:200]}\n\nTry testing Ollama manually: {curl_cmd}")
                    return
            except requests.exceptions.Timeout as e:
                self.error.emit(f"Model test timed out after 5 minutes.\nThe model '{self.model}' might be:\n- Still loading into GPU memory\n- Too large for your system\n- Not compatible\n\nError: {str(e)}\n\nTry testing manually: ollama run {self.model}")
                return
            except requests.exceptions.ConnectionError as e:
                self.error.emit(f"Connection error during model test: {str(e)}\nMake sure Ollama is running.")
                return
            except Exception as e:
                self.error.emit(f"Model test error: {str(e)}\n\nTry testing manually: ollama run {self.model}")
                return
            
            translated_text = ''
            total_chunks = (len(self.text) + self.max_length - 1) // self.max_length
            
            for chunk_idx, start in enumerate(range(0, len(self.text), self.max_length), 1):
                end = min(start + self.max_length, len(self.text))
                chunk = self.text[start:end]
                
                progress_percent = int((chunk_idx / total_chunks) * 100)
                self.progress_update.emit(f"Translating chunk {chunk_idx}/{total_chunks}...", progress_percent)
                self.chunk_start.emit(f"Translating chunk {chunk_idx}/{total_chunks}...")
                
                try:
                    self.chunk_start.emit(f"Sending request to Ollama for chunk {chunk_idx}/{total_chunks}...")
                    
                    ollama_url = "http://localhost:11434/api/chat"
                    target_lang = self.target_language.strip().lower()
                    target_lang_capitalized = target_lang.capitalize()
                    
                    language_map = {
                        'spanish': 'español',
                        'italian': 'italiano',
                        'german': 'deutsch',
                        'french': 'français',
                        'portuguese': 'português',
                        'dutch': 'nederlands',
                        'russian': 'русский',
                        'chinese': '中文',
                        'japanese': '日本語',
                        'korean': '한국어',
                        'arabic': 'العربية',
                        'polish': 'polski',
                        'greek': 'ελληνικά',
                        'turkish': 'türkçe',
                    }
                    
                    target_lang_native = language_map.get(target_lang, target_lang_capitalized)
                    
                    payload = {
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": f"CRITICAL INSTRUCTION: You are a translator. You MUST translate text to {target_lang_capitalized} ({target_lang_native}). Output ONLY in {target_lang_capitalized} ({target_lang_native})."
                            },
                            {
                                "role": "user",
                                "content": f"Translate this text from its original language to {target_lang_capitalized} ({target_lang_native}) ONLY. Output the translation ONLY in {target_lang_capitalized} ({target_lang_native}):\n\n{chunk}"
                            }
                        ],
                        "stream": False
                    }
                    
                    timeout_seconds = 180
                    
                    self.chunk_start.emit(f"Translating to {target_lang_capitalized} ({target_lang_native})")
                    
                    headers = {'Content-Type': 'application/json'}
                    try:
                        http_response = requests.post(
                            ollama_url,
                            json=payload,
                            headers=headers,
                            timeout=(10, timeout_seconds)
                        )
                    except requests.exceptions.Timeout as e:
                        self.error.emit(f"Request timed out after {timeout_seconds} seconds for chunk {chunk_idx}.\nThis might mean:\n- The model is still loading\n- The request is too large\n- Ollama is not responding\n\nError: {str(e)}")
                        return
                    except requests.exceptions.ConnectionError as e:
                        self.error.emit(f"Connection error for chunk {chunk_idx}: {str(e)}\nMake sure Ollama is still running.")
                        return
                    
                    if http_response.status_code != 200:
                        error_text = http_response.text[:200] if http_response.text else "No error details"
                        self.error.emit(f"Ollama API error for chunk {chunk_idx}: Status {http_response.status_code}\nResponse: {error_text}\n\nCheck Ollama logs for more details.")
                        return
                    
                    response = http_response.json()
                    self.chunk_start.emit(f"Received response from Ollama for chunk {chunk_idx}/{total_chunks}")
                    
                    if response and 'message' in response and 'content' in response['message']:
                        content = response['message']['content'].strip()
                        
                        prefixes_to_remove = [
                            f"translation:",
                            f"in {target_lang_capitalized.lower()}:",
                            f"{target_lang_capitalized.lower()}:",
                            f"{target_lang_capitalized}:",
                            "translation to",
                            "translated:",
                            "here's the translation:",
                            "here is the translation:",
                        ]
                        
                        content_lower = content.lower()
                        for prefix in prefixes_to_remove:
                            if content_lower.startswith(prefix):
                                content = content[len(prefix):].strip()
                                content = content.lstrip(":-\n").strip()
                                break
                        
                        lines = content.split('\n')
                        cleaned_lines = []
                        skip_patterns = [
                            'original:',
                            'text:',
                            'source:',
                        ]
                        
                        in_translation = True
                        for line in lines:
                            line_lower = line.lower().strip()
                            if any(pattern in line_lower and ':' in line_lower for pattern in skip_patterns):
                                in_translation = False
                                continue
                            if target_lang_capitalized.lower() in line_lower and ':' in line_lower:
                                in_translation = True
                                if ':' in line:
                                    line = line.split(':', 1)[1].strip()
                            if in_translation and line.strip():
                                cleaned_lines.append(line)
                        
                        final_content = '\n'.join(cleaned_lines).strip() if cleaned_lines else content.strip()
                        
                        if final_content:
                            translated_text += final_content + '\n\n'
                            self.chunk_complete.emit(f"Chunk {chunk_idx}/{total_chunks} completed")
                        else:
                            self.error.emit(f"Empty or invalid response from Ollama for chunk {chunk_idx}")
                            return
                    else:
                        self.error.emit(f"Unexpected response format from Ollama for chunk {chunk_idx}: {str(response)}")
                        return
                except requests.exceptions.Timeout:
                    self.error.emit(f"Timeout: Ollama did not respond within {timeout_seconds} seconds for chunk {chunk_idx}. The model might still be loading. Try again in a moment.")
                    return
                except requests.exceptions.RequestException as e:
                    self.error.emit(f"Connection error translating chunk {chunk_idx}: {str(e)}")
                    return
                except Exception as e:
                    self.error.emit(f"Error translating chunk {chunk_idx}: {str(e)}")
                    return
            
            self.progress_update.emit("Saving translated text...", 95)
            self.finished.emit(translated_text)
            
        except Exception as e:
            self.error.emit(f"Translation error: {str(e)}")

class PDFDropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setAcceptDrops(True)
        
        self.setStyleSheet("""
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                font-size: 13px;
            }
            QLineEdit, QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: #ffffff;
                selection-background-color: #4a9eff;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #4a9eff;
                background-color: #fafafa;
            }
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #3a8eef;
            }
            QPushButton:pressed {
                background-color: #2a7edf;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                text-align: center;
                background-color: #f5f5f5;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4a9eff;
                border-radius: 6px;
            }
            QLabel {
                color: #333333;
                font-weight: 500;
            }
            QTextEdit[readOnly="true"] {
                background-color: #f9f9f9;
                border: 2px solid #e0e0e0;
            }
        """)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Drag and drop a PDF file here.")
        self.text_edit.setReadOnly(True)
        
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("Enter target language (e.g., Spanish, German, etc.)")

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Enter Ollama model name (e.g., llama2, mistral, codellama)")
        
        self.btn_translate = QPushButton("Translate Text")
        self.btn_translate.clicked.connect(self.prompt_for_translation)
        
        self.btn_open_file = QPushButton("Open Translated Text File")
        self.btn_open_file.clicked.connect(self.open_translated_file)
        self.btn_open_file.setEnabled(False)

        self.status_label = QLabel('<span style="color: #333333;">Ready</span>')
        self.status_label.setTextFormat(1)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)

        layout = QGridLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        layout.addWidget(QLabel("PDF File:"), 0, 0)
        layout.addWidget(self.text_edit, 0, 1, 1, 2)
        layout.addWidget(QLabel("Language:"), 1, 0)
        layout.addWidget(self.language_input, 1, 1, 1, 2)
        layout.addWidget(QLabel("Model:"), 2, 0)
        layout.addWidget(self.model_input, 2, 1, 1, 2)
        layout.addWidget(self.btn_translate, 3, 2)
        layout.addWidget(QLabel("Status:"), 4, 0)
        layout.addWidget(self.status_label, 4, 1, 1, 2)
        layout.addWidget(self.progress_bar, 5, 0, 1, 3)
        layout.addWidget(self.output_console, 6, 0, 1, 3)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_open_file)
        layout.addLayout(button_layout, 7, 0, 1, 3)
        
        self.setLayout(layout)
        self.setWindowTitle('PDF Translator')
        self.resize(700, 500)

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

    def prompt_for_translation(self):
        if hasattr(self, 'file_path') and os.path.exists(self.file_path):
            self.status_label.setText('<span style="color: #333333;">Reading PDF...</span>')
            QApplication.processEvents()
            
            text = self.read_pdf(self.file_path)
            model = self.model_input.text().strip()
            target_language = self.language_input.text().strip()
            
            if not target_language:
                self.status_label.setText('<span style="color: #333333;">Ready</span>')
                self.output_console.append("Please enter a target language.")
                return
            
            if not model:
                self.status_label.setText('<span style="color: #333333;">Ready</span>')
                self.output_console.append("Please enter an Ollama model name.")
                return

            target_lang_normalized = target_language.strip().lower()
            language_map = {
                'spanish': 'español',
                'italian': 'italiano',
                'german': 'deutsch',
                'french': 'français',
                'portuguese': 'português',
                'dutch': 'nederlands',
                'chinese': '中文',
                'japanese': '日本語',
                'korean': '한국어',
            }
            target_lang_native = language_map.get(target_lang_normalized, target_lang_normalized)
            
            self.output_console.append(f"Ready to translate PDF using model: {model}")
            self.output_console.append(f"Target language: {target_lang_normalized.capitalize()} ({target_lang_native})")
            self.output_console.append(f"PDF text length: {len(text)} characters")
            
            self.translate_text(text, model, target_lang_normalized)
        else:
            self.status_label.setText('<span style="color: #333333;">Ready</span>')
            self.output_console.append("Please drop a valid PDF file first.")

    def translate_text(self, text, model, target_language):
        self.btn_translate.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.target_language = target_language
        self.original_file_path = self.file_path
        
        self.translation_worker = TranslationWorker(text, model, target_language, self.file_path)
        self.translation_worker.progress_update.connect(self.on_progress_update)
        self.translation_worker.chunk_start.connect(self.on_chunk_start)
        self.translation_worker.chunk_complete.connect(self.on_chunk_complete)
        self.translation_worker.finished.connect(self.on_translation_finished)
        self.translation_worker.error.connect(self.on_translation_error)
        self.translation_worker.start()
    
    def on_progress_update(self, status_message, progress_percent):
        if '<' not in status_message or '>' not in status_message:
            self.status_label.setText(f'<span style="color: #333333;">{status_message}</span>')
        else:
            self.status_label.setText(status_message)
        self.progress_bar.setValue(progress_percent)
    
    def on_chunk_start(self, message):
        self.output_console.append(message)
    
    def on_chunk_complete(self, message):
        self.output_console.append(message)
    
    def on_translation_finished(self, translated_text):
        try:
            if hasattr(self, 'original_file_path') and self.original_file_path:
                base_name = os.path.splitext(os.path.basename(self.original_file_path))[0]
                output_dir = os.path.dirname(self.original_file_path)
                target_lang_lower = self.target_language.lower().replace(' ', '_')
                output_filename = f"{base_name}_{target_lang_lower}.txt"
                output_file = os.path.join(output_dir, output_filename) if output_dir else output_filename
            else:
                target_lang_lower = self.target_language.lower().replace(' ', '_') if hasattr(self, 'target_language') else 'translated'
                output_file = f'translated_text_{target_lang_lower}.txt'
            
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(translated_text.strip())
            
            self.output_file_path = output_file
            
            checkmark = "✓"
            self.status_label.setText(f'<span style="color: #22c55e; font-weight: bold; font-size: 14px;">{checkmark} Translation complete!</span>')
            self.progress_bar.setValue(100)
            self.output_console.append(f"Translation complete! Output saved to '{os.path.basename(output_file)}'")
            self.btn_open_file.setEnabled(True)
            self.btn_translate.setEnabled(True)
            self.text_edit.setPlaceholderText("Drag and drop a PDF file here.")
            self.text_edit.setText("")
        except Exception as e:
            self.on_translation_error(f"Error saving file: {str(e)}")
    
    def on_translation_error(self, error_message):
        self.status_label.setText('<span style="color: #ef4444; font-weight: bold;">✗ Error occurred</span>')
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.btn_translate.setEnabled(True)
        self.output_console.append(f"Error during translation: {error_message}")
        self.output_console.append("Make sure Ollama is running and the model is available.")
        
        model = self.model_input.text().strip() if hasattr(self, 'model_input') else "unknown"
        QMessageBox.critical(self, "Translation Error", 
                           f"An error occurred during translation:\n{error_message}\n\nMake sure Ollama is running and the model '{model}' is available.")

    def open_translated_file(self):
        if hasattr(self, 'output_file_path') and os.path.exists(self.output_file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(self.output_file_path)))
        else:
            default_file = 'translated_text.txt'
            if os.path.exists(default_file):
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(default_file)))
            else:
                QMessageBox.warning(self, "File Not Found", "The translated file could not be found.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = PDFDropWidget()
    mainWin.show()
    sys.exit(app.exec_())
