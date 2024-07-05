import os
import PyPDF2
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
from colorama import Fore, Style, init

# Initialize Colorama
init()

# Load environment variables from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def read_pdf(file_path):
    """ Read text from a PDF file """
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
    return text

def calculate_cost(prompt_tokens, completion_tokens, model):
    """ Calculate cost based on model and token usage """
    if model == "gpt-3.5-turbo":
        input_cost = prompt_tokens * 0.50 / 1000000
        output_cost = completion_tokens * 1.50 / 1000000
    elif model == "gpt-4o":
        input_cost = prompt_tokens * 5.00 / 1000000
        output_cost = completion_tokens * 15.00 / 1000000
    total_cost = input_cost + output_cost
    return input_cost, output_cost, total_cost

def translate_text(text, model, target_language):
    """ Translate text using OpenAI's API in chunks due to length constraints """
    max_length = 5000
    translated_text = ''
    progress_bar = tqdm(total=len(text), desc="Translating", colour="blue")
    
    estimated_prompt_tokens = (len(text) / 2000) * 700  # Rough estimation
    estimated_completion_tokens = estimated_prompt_tokens * 0.9
    estimated_input_cost, estimated_output_cost, estimated_total_cost = calculate_cost(
        estimated_prompt_tokens, estimated_completion_tokens, model)
    
    print(Fore.MAGENTA + f"Estimated API calls: {(len(text) + max_length - 1) // max_length}")
    print(Fore.YELLOW + f"Estimated Cost: Input ${estimated_input_cost:.6f}, Output ${estimated_output_cost:.6f}, Total ${estimated_total_cost:.6f}" + Style.RESET_ALL)
    
    proceed = input(Fore.CYAN + "Proceed with translation? (yes/no) [yes]: " + Style.RESET_ALL).strip().lower()
    if proceed not in ['', 'y', 'yes']:
        return ""
    
    actual_prompt_tokens = actual_completion_tokens = 0
    for start in range(0, len(text), max_length):
        end = start + max_length
        chunk = text[start:end]
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": f"Translate the following text to {target_language}:\n\n{chunk}"}],
            max_tokens=4096
        )
        translated_text += response.choices[0].message.content.strip() + '\n\n'
        actual_prompt_tokens += response.usage.prompt_tokens
        actual_completion_tokens += response.usage.completion_tokens
        progress_bar.update(end - start)
    
    progress_bar.close()
    
    # Calculate and display actual cost after translation
    actual_input_cost, actual_output_cost, actual_total_cost = calculate_cost(actual_prompt_tokens, actual_completion_tokens, model)
    print(Fore.YELLOW + f"Tokens: Prompt: {actual_prompt_tokens}, Completion: {actual_completion_tokens}, Total: {actual_prompt_tokens + actual_completion_tokens}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"Cost: Prompt ${actual_input_cost:.6f}, Completion ${actual_output_cost:.6f}, Total ${actual_total_cost:.6f}" + Style.RESET_ALL)
    
    return translated_text

def main():
    file_path = input(Fore.GREEN + "Please enter the path to the PDF file: " + Style.RESET_ALL)
    if not os.path.exists(file_path):
        print(Fore.RED + "File does not exist." + Style.RESET_ALL)
        return
    
    print(Fore.MAGENTA + "Reading PDF..." + Style.RESET_ALL)
    text = read_pdf(file_path)
    
    model = "gpt-3.5-turbo"  # Default model
    model_input = input(Fore.CYAN + "Enter '/gpt3' or '/gpt4' to switch models or press Enter to continue with GPT-3.5-turbo: " + Style.RESET_ALL).strip().lower()
    if model_input == "/gpt3":
        model = "gpt-3.5-turbo"
    elif model_input == "/gpt4":
        model = "gpt-4o"
    
    target_language = input(Fore.CYAN + "Enter the target language for translation (e.g., German, French, Spanish): " + Style.RESET_ALL).strip()
    
    translated_text = translate_text(text, model, target_language)
    if not translated_text:
        print(Fore.RED + "Translation canceled." + Style.RESET_ALL)
        return

    output_file = 'translated_text.txt'
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(translated_text)
    
    print(Fore.MAGENTA + f"Translation complete! Check the translated text in '{output_file}'." + Style.RESET_ALL)

if __name__ == "__main__":
    main()
