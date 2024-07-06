# 📄 GPT Translation Script for large PDF files

This script provides an automated way to translate the text content of large PDF files from any language to any language using OpenAI's GPT models.

**Update:**  It now features a PyQt5 GUI that allows for drag-and-drop PDF functionality, making it more user-friendly and interactive. The GUI includes features like real-time progress updates, model selection, and cost prediction before translations are processed.

## 🌟 Features

- **🖱 Drag-and-Drop Interface**: Easily drag and drop PDF files into the GUI.
- **📖 PDF Reading**: Extracts text from PDF files.
- **🌍 Language Translation**: Translates text to any language utilizing OpenAI's GPT models with input for target language.
- **🔄 Model Selection**: Users can choose between GPT-3.5-turbo and GPT-4o models through a dropdown menu.
- **💰 Cost Estimation**: Provides an estimated and actual cost analysis based on the number of tokens processed.
- **📈 Progress Tracking**: Shows translation progress in the GUI's console window.
- **✅ Interactive Confirmation**: Users can confirm or cancel the translation based on the estimated costs directly from the GUI.
- **📝 File Output**: Translated text is saved to `translated_text.txt`, with an option to open this file directly from the GUI.

## 📋 Prerequisites

Before running the script, ensure the following prerequisites are met:
- Python 3.6 or higher is installed on your system.
- An active OpenAI API key is required.
- Python libraries: `PyPDF2`, `openai`, `tqdm`, `colorama`, `python-dotenv`, `PyQt5`

## ⚙️ Installation

1. **Clone the repository**:
   ```
   git clone https://github.com/loyft/pdf-gpt.git
   cd pdf-gpt
   ```

2. **Install required libraries**:
   ```
   pip install PyPDF2 openai tqdm colorama python-dotenv PyQt5
   ```

3. **Set up environment variables**:
   
  - Create a `.env` file in the script directory.
  - Add your OpenAI API key to the `.env` file:

     ```
    OPENAI_API_KEY=your_api_key_here
     ```

## 🚀 Usage

To use the script, navigate to the script's directory and run:
```
python main.py
```

### Steps

1. **Drag and drop a PDF file** into the GUI area designated for it.
2. **Select the translation model** from the dropdown menu.
3. **Enter the target language** for translation.
4. **Review the estimated cost** displayed in the GUI's console area.
5. **Confirm to proceed** with the translation by clicking the translate button.
6. **Open the translated text file** using the button provided once the translation is complete.

## 📤 Output

The script will save the translated text into a file named `translated_text.txt` in the script's directory. It also displays the cost details and the number of tokens used for the translation in the GUI's console.

## 🖥 System Compatibility

- **Tested on macOS**: This application has been tested on macOS and might require modifications to run on other operating systems.

## 🤝 Contributing

Contributions to enhance the script, improve efficiency, or add new features are welcome. Please fork the repository and submit a pull request with your updates.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, raise an issue in the repository.
