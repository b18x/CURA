# PDF Semi-Structured Data Extraction and Analysis with Anthropics Claude API
# Created to search for three types of information for headers and create an Excel file with the results
# Version: 1.0
# Date: 2024-10-15
# Creator: Juhani Merilehto - @juhanimerilehto
# Sponsor: Jyväskylä University of Applied Sciences (JAMK), Likes institute


import os
import fitz  # PyMuPDF for PDF handling
from openai import OpenAI
import pandas as pd
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Log level set to INFO, change to DEBUG for more verbosity
    format='%(asctime)s - %(levelname)s - %(message)s',  # Standard logging format with timestamps
    handlers=[
        logging.FileHandler("script.log"),  # Log to a file called 'script.log'
        logging.StreamHandler()  # Also output logs to the console
    ]
)

# Load environment variables from .env file
load_dotenv()

client = OpenAI(api_key="")  

logging.info("Script is running")  # Log that the script has started

def extract_and_query_page(pdf_path, page_number, api_key, max_tokens=4000):  # Adjusted max_tokens default to 4000
    # Open the PDF document
    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number)  # Load the specific page
        text = page.get_text()  # Extract text from the page
        logging.info(f"Extracting text from page {page_number+1}/{len(doc)}")  # Log page extraction progress
        logging.debug(f"Extracted text: {text[:50]}")  # Log first 50 characters of the extracted text for debugging
        response = query_openai_api(text, max_tokens)
        return response

# Query the OpenAI API using provided text and the system's API key
def query_openai_api(text, max_tokens=4000):  # Adjusted max_tokens to 4000 to match input limits
    # System prompt to set the context for OpenAI
    system_prompt = "You are an AI assistant helping to organize data from a PDF file."

    # User-specific prompt to instruct OpenAI on how to analyze the text
    human_prompt = f"""Analyze the following text from a PDF report and extract pairs of "Chemical Trade Names" and "CAS Numbers".

Text:
{text}

Present your findings in a structured format with each entry separated by commas. Each entry should list the Chemical Trade Name and CAS Number.

Chemical Names are natural words, such as "Fluoroacetamide", "1,1,1,2-Tetrachloroethane", "2,4,5-T and its salts and esters", "1,2-dibromoethane (EDB) " etc.
CAS Numbers are unique identifiers for chemicals, such as "640-19-7", "13071-79-9", "630-20-6", etc. CAS Numbers never contain words.

Format your response as: Chemical Trade Name, CAS Number. Examples: 
Mercury compounds, 71-43-2
Ethanol, 64-17-5

ALWAYS REMEMBER THE FOLLOWING RULES:
1. If multiple variations exist (e.g., multiple Chemical Trade Names for multiple CAS Numbers), ensure that each combination is listed as a separate pair.
2. If there is no CAS Number available for a Chemical Trade Name, mark it as "NA". Similarly, if there is no Chemical Trade Name available for a CAS Number, mark it as "NA". NEVER, IN ANY SCENARIO, HALLUCINATE DATA.
3. The format MUST HAVE the two columns and ONLY the two columns. Be extremely accurate and ensure the format is consistent.
4. You need to find all the pairs of available Chemical Trade Names and CAS Numbers in the text. DONT MISS ANY.
5. If the entire text does not contain any Chemical Trade Names or CAS Numbers, respond with "N/A,N/A". Never write full-text answers explaining yourself.

It is extremely important that you perform well on this job. Otherwise, I will lose my job and 1000 grandmothers will die!"""

    try:
        # Call the OpenAI API with the prompt and message
        response = client.chat.completions.create(
            model="gpt-4.5-preview",  # Specify the OpenAI model to use
            messages=[
                {"role": "system", "content": system_prompt},  # System prompt
                {"role": "user", "content": human_prompt}  # User prompt
            ],
            max_tokens=max_tokens,  # Limit the response to a certain number of tokens
        )
        logging.debug(f"Raw API response: {response}")  # Log the raw response content

        # Access the content field
        return response.choices[0].message.content  # Return the content field from the API response
    except Exception as e:
        logging.error(f"Error in API response: {e}")  # Log the error in case of API failure
        return f"Error in API response: {e}"  # Return the error message as the response

# Parse the Claude response and convert it into a DataFrame-friendly format
def parse_gpt_response_to_dataframe(response_content, filename, all_data):
    lines = response_content.strip().split('\n')  # Split response into lines
    for line in lines:
        if line:  # Ensure line is not empty
            # Split by commas and keep only the first two elements: Trade Name, CAS Number
            data = [element.strip() for element in line.split(',')][:2]
            data.append(filename)  # Append the filename to the data
            all_data.append(data)  # Append the parsed data to the list
    return all_data  # Return the updated list

# Process all PDF files in the input folder and output results to Excel
def process_pdfs(input_folder, output_folder, api_key, max_tokens=4000):  # max_tokens set to 4000 for input/output control
    for filename in sorted(os.listdir(input_folder)):  # Iterate over all files in the input folder
        if filename.lower().endswith('.pdf'):  # Process only PDF files

            # Sanitize the filename for Excel file creation (remove unwanted characters)
            sanitized_filename = filename.replace('.PDF', '').replace('.pdf', '')
            sanitized_filename = sanitized_filename.replace("+", "_").replace(",", "").replace(" ", "_")

            pdf_path = os.path.join(input_folder, filename)  # Construct full path to PDF file
            all_data = []  # Initialize list to accumulate data from all pages
            logging.info(f"Processing PDF file: {filename}")  # Log the start of processing for the file
            with fitz.open(pdf_path) as doc:  # Open the PDF file
                for page_number in range(len(doc)):  # Iterate over all pages in the document
                    # Extract text from each page and query the Claude API
                    response_content = extract_and_query_page(pdf_path, page_number, api_key, max_tokens)
                    # Parse API response and add it to the accumulated data
                    all_data = parse_gpt_response_to_dataframe(response_content, sanitized_filename, all_data)

            # Once all pages are processed, create a DataFrame from the accumulated data
            df = pd.DataFrame(all_data, columns=['trade_name', 'cas', 'filename'])

            excel_filename = sanitized_filename + '.xlsx'  # Define the Excel filename
            excel_path = os.path.join(output_folder, excel_filename)  # Define the path for saving the Excel file

            # Save the DataFrame to an Excel file
            df.to_excel(excel_path, index=False)

            logging.info(f"Processed {filename} and saved Excel file to {excel_path}")  # Log the successful file save

# Configuration and execution using environment variables
api_key = os.getenv('OPENAI_API_KEY')  # Retrieve API key from environment variables
input_folder = os.getenv('PDF_INPUT_FOLDER', './PDFs')  # Default input folder is './PDFs' if not set
output_folder = os.getenv('EXCEL_OUTPUT_FOLDER', './ExcelFiles')  # Default output folder is './ExcelFiles' if not set
max_tokens = int(os.getenv('MAX_TOKENS', 4000))  # Set the token limit from environment or default to 4000

# Ensure the output directory exists; if not, create it
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Start processing the PDFs
process_pdfs(input_folder, output_folder, api_key, max_tokens)