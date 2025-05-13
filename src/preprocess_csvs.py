import os
import csv
from openai import OpenAI
import logging
from dotenv import load_dotenv
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Log level set to INFO, change to DEBUG for more verbosity
    format='%(asctime)s - %(levelname)s - %(message)s',  # Standard logging format with timestamps
    handlers=[
        logging.FileHandler("script.log"),  # Log to a file called 'script.log'
        logging.StreamHandler()  # Also output logs to the console
    ]
)

logging.info("Script is running")  # Log that the script has started

def extract_and_query_csv_chunk(csv_path, chunk_start, chunk_size, api_key, max_tokens=4000):
    # Read the specified chunk from the CSV file
    chunk_lines = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            # Skip to the starting point of our chunk
            csv_reader = csv.reader(csv_file)
            for i, _ in enumerate(csv_reader):
                if i >= chunk_start:
                    break
            
            # Read the chunk_size number of lines
            for i, row in enumerate(csv_reader):
                if i >= chunk_size:
                    break
                # Convert row to string and add to chunk
                chunk_lines.append(','.join(row))
    except Exception as e:
        logging.error(f"Error reading CSV chunk: {e}")
        return "Error reading CSV"
    
    # Convert the chunk to text
    text = '\n'.join(chunk_lines)
    
    logging.info(f"Extracting text from lines {chunk_start+1}-{chunk_start+len(chunk_lines)}")
    logging.debug(f"Extracted text sample: {text[:50]}")
    
    # Process with OpenAI
    response = query_openai_api(text, max_tokens, extraction_prompt)
    validated_response = query_openai_api(response, max_tokens, validation_prompt)
    return validated_response

# Query the OpenAI API using provided text and the system's API key
def query_openai_api(context, max_tokens, human_prompt):  # Adjusted max_tokens to 4000 to match input limits
    # System prompt to set the context for OpenAI
    system_prompt = "You are a useful, correct AI assistant helping to organize data from a CSV file and validate it."

    try:
        # Call the OpenAI API with the prompt and message
        response = client.chat.completions.create(
            model="gpt-4.5-preview",  # Specify the OpenAI model to use
            messages=[
                {"role": "system", "content": system_prompt},  # System prompt
                {"role": "user", "content": human_prompt + context}  # User prompt
            ],
            max_tokens=max_tokens,  # Limit the response to a certain number of tokens
        )
        logging.debug(f"Raw API response: {response}")  # Log the raw response content

        # Access the content field
        print(type(response.choices[0].message.content))
        return response.choices[0].message.content  # Return the content field from the API response
    except Exception as e:
        logging.error(f"Error in API response: {e}")  # Log the error in case of API failure
        return f"Error in API response: {e}"  # Return the error message as the response

# Parse the Claude response and convert it into a DataFrame-friendly format
def parse_gpt_response_to_json(response_content, regulation, chemicals_list):
    lines = response_content.strip().split('\n')  # Split response into lines
    for line in lines:
        if line:  # Ensure line is not empty
             # Split by commas and keep only the first two elements: Trade Name, CAS Number
            parts = [element.strip() for element in line.split('$')][:2]
            if len(parts) == 2:
                chemical_entry = {
                    "chemical_name": parts[0],
                    "CAS": parts[1],
                    "regulation": regulation
                }
                chemicals_list.append(chemical_entry)
    
    print(f"Current chemicals count: {len(chemicals_list)}")
    return chemicals_list  # Return the updated list

# Process all CSV files in the input folder and output results to JSON
def process_csvs(input_folder, output_folder, api_key, chunk_size, max_tokens=4000):  # max_tokens set to 4000 for input/output control
    for filename in sorted(os.listdir(input_folder)):  # Iterate over all files in the input folder
        if filename.lower().endswith('.csv'):  # Process only CSV files

            # Sanitize the filename for Excel file creation (remove unwanted characters)
            sanitized_filename = filename.replace('.CSV', '').replace('.csv', '')
            sanitized_filename = sanitized_filename.replace("+", "_").replace(",", "").replace(" ", "_")

            csv_path = os.path.join(input_folder, filename)  # Construct full path to CSV file
            chemicals_list = []  # Initialize list to accumulate data from all pages
            logging.info(f"Processing CSV file: {filename}")  # Log the start of processing for the file
            
            # Count total lines in the CSV file
            with open(csv_path, 'r', encoding='utf-8') as f:
                total_lines = sum(1 for _ in f)
            
            logging.info(f"Total lines in CSV: {total_lines}")
            
            # Process the CSV in chunks
            chunk_start = 0
            while chunk_start < total_lines:
                logging.info(f"Processing chunk starting at line {chunk_start}")
                
                # Extract text from current chunk and query the OpenAI API
                response_content = extract_and_query_csv_chunk(
                    csv_path, chunk_start, chunk_size, api_key, max_tokens
                )
                
                # Parse API response and add it to the accumulated data
                chemicals_list = parse_gpt_response_to_json(
                    response_content=response_content, 
                    regulation=sanitized_filename, 
                    chemicals_list=chemicals_list
                )
                
                # Move to the next chunk
                chunk_start += chunk_size

            # Create final JSON structure
            json_output = {"chemicals": chemicals_list}

            # Define the JSON filename and path
            json_filename = sanitized_filename + '.json'
            json_path = os.path.join(output_folder, json_filename)

            # Save the data to a JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_output, f, indent=4)

            logging.info(f"Processed {filename} and saved JSON file to {json_path}")

# Prompt used later to extract information
extraction_prompt = f"""Analyze the following CSV table and extract pairs of "Chemical Trade Names" and "CAS Numbers".

Present your findings in a structured format with each entry separated by dollar signs . Each entry should list the Chemical Trade Name and CAS Number.

Chemical Names are natural words, such as "Fluoroacetamide", "1,1,1,2-Tetrachloroethane", "2,4,5-T and its salts and esters", "1,2-dibromoethane (EDB) " etc.
CAS Numbers are unique identifiers for chemicals, such as "640-19-7", "13071-79-9", "630-20-6", etc. CAS Numbers never contain words.

Format your response as: Chemical Trade Name $ CAS Number. Examples: 
Mercury compounds $ 71-43-2
Ethanol $ 64-17-5

ALWAYS REMEMBER THE FOLLOWING RULES:
1. If multiple variations exist (e.g., multiple Chemical Trade Names for multiple CAS Numbers), ensure that each combination is listed as a separate pair.
2. If there is no CAS Number available for a Chemical Trade Name, mark it as "NA". Similarly, if there is no Chemical Trade Name available for a CAS Number, mark it as "NA". NEVER, IN ANY SCENARIO, HALLUCINATE DATA. 
3. The format MUST HAVE the two columns and ONLY the two columns. Be extremely accurate and ensure the format is consistent.
4. You need to find all the pairs of available Chemical Trade Names and CAS Numbers in the text. DONT MISS ANY.
5. If the entire text does not contain any Chemical Trade Names or CAS Numbers, respond with "N/A,N/A". 
6. Never write full-text answers explaining yourself. Only provide the requested pairs. If you are unsure, only write N/A for both columns.

It is extremely important that you perform well on this job. Otherwise, I will lose my job and 1000 grandmothers will die!

Here is the text to analyze:"""

# Prompt used later to validate information
validation_prompt = """Analyze the following list that contains chemical names and their CAS numbers in the format:

chemical_name $ CAS
chemical_name $ CAS

Your job is to go over the list, keep all valid combinations, and improve invalid combinations. Generally, all combinations are valid, and should therefore be kept. Only change combinations in any of these cases:

CRITERIA FOR INVALID COMBINATIONS

1. Grouped Chemicals: If the chemical name refer to multiple chemicals, generate pairs of "chemical_name $ CAS" for each individual chemical. 
2. Entries containing "N/A": If only chemical_name is "N/A", fill in the missing chemical name from the CAS number. Vice versa, if only CAS number is "N/A", fill in the missing CAS number from the chemical name. If both chemical name and CAS number are "N/A", remove the entry.

EXAMPLES OF INVALID COMBINATIONS

"2,4,5-T and its salts and esters $ 93-76-5" --> invalid because it groups multiple chemicals together. Change to "2,4,5-T $ 93-76-5", “Sodium trichlorophenoxyacetate $ 88-85-7”, “Dimethylammonium trichlorophenoxyacetate $ 2008-39-1”, “Isooctyl 2,4,5-trichlorophenoxyacetate $ 25168-26-7”
"Asbestos: Tremolite $ N/A" --> invalid because it is missing the CAS number. Change to "Asbestos: Tremolite $ 77536-68-6"        
"N/A $ N/A" --> invalid because it does not contain any valid data. Remove the entry.

ALWAYS REMEMBER THE FOLLOWING RULES:
1. Only change invalid combinations. Keep all valid combinations. If you are unsure, keep the entry as it is.
1. Each entry is placed in a new line and should be separated by dollar signs and formatted as: Chemical Name $ CAS Number. Never produce any other format, never produce free-text explaining yourself.
2. NEVER, IN ANY SCENARIO, HALLUCINATE DATA. If you are unsure about an entry, keep it as it is.
4. Be extremely accurate and ensure the format is consistent across all entries.

It is extremely important that you perform well on this job. Otherwise, I will lose my job and 1000 grandmothers will die!

Here is the text to analyze and improve:"""

# Load environment variables from .env file
load_dotenv()

# Configuration and execution using environment variables
api_key = os.getenv('OPENAI_API_KEY')  # Retrieve API key from environment variables
input_folder = os.getenv('CSV_INPUT_FOLDER')  
output_folder = os.getenv('JSON_OUTPUT_FOLDER')  
max_tokens = int(os.getenv('MAX_TOKENS', 4000))  # Set the token limit from environment or default to 4000
chunk_size = int(os.getenv('CSV_CHUNK_SIZE', 15))  # Set the chunk size from environment or default to 1000

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ensure the output directory exists; if not, create it
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Start processing the CSVs
process_csvs(input_folder, output_folder, api_key, chunk_size, max_tokens)