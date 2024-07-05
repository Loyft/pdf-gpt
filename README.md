# GPT Translation Script for PDF

This script provides an automated way to translate the text content of large PDF files from any language to any language using OpenAI's language models. It features an interactive console interface that allows users to choose between different GPT models, receive cost estimates before processing, and confirm continuation based on those estimates.

## Features

- **PDF Reading**: Extracts text from PDF files.
- **Language Translation**: Translates text to any language utilizing OpenAI's GPT models.
- **Model Selection**: Users can switch between GPT-3.5-turbo and GPT-4 models.
- **Cost Estimation**: Provides an estimated and actual cost analysis based on the number of tokens processed.
- **Progress Tracking**: Shows translation progress via a progress bar.
- **Interactive Confirmation**: Users can confirm or cancel the translation based on the estimated costs.

## Prerequisites

Before running the script, ensure the following prerequisites are met:
- Python 3.6 or higher is installed on your system.
- An active OpenAI API key is required.
- Python libraries: `PyPDF2`, `openai`, `tqdm`, `colorama`, `python-dotenv`

## Installation

1. **Clone the repository**:
   ```
   git clone https://github.com/loyft/pdf-gpt.git
   cd pdf-gpt
   ```

2. **Install required libraries**:
   ```
   pip install PyPDF2 openai tqdm colorama python-dotenv
   ```

3. **Set up environment variables**:
   
  - Create a `.env` file in the script directory.
  - Add your OpenAI API key to the `.env` file:

     ```
    OPENAI_API_KEY='your_api_key_here'
     ```

## Usage

To use the script, navigate to the script's directory and run:
```
python main.py
```

### Steps

1. **Input the path to your PDF file** when prompted.
2. **Choose the model** for translation by entering `/gpt3` for gpt-3.5-turbo or `/gpt4` for gpt-4o. If no input is given, the script defaults to using GPT-3.5-turbo.
3. **Review the cost estimate** that will be displayed based on the text content of the PDF. (more or less accurate depending on original and target language)
4. **Confirm to proceed** with translation; the default option is 'yes', simply press Enter to continue, or type 'n' or 'no' to cancel.
5. **Check the results** in the output file named `translated_text.txt` once the translation is complete.

## Output

The script will output the translated text into a file named `translated_text.txt` in the script's directory. It also prints out the cost details and the number of tokens used for the translation.

## Contributing

Contributions to enhance the script, improve efficiency, or add new features are welcome. Please fork the repository and submit a pull request with your updates.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, raise an issue in the repository.
