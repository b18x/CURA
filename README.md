# CURA: LLM-based Chemical Information Extraction and Graph-Based RAG

## Overview
This project focuses on developing a system to extract chemical information (names, CAS numbers, regulations) from PDF documents and unstructured text using Large Language Models (LLMs). The extracted data is then structured and loaded into a Neo4j graph database to enable advanced querying and Retrieval Augmented Generation (RAG) capabilities through a Streamlit user interface. This work forms the basis of a Master Thesis in Information Systems.

## Features
* PDF text extraction from documents.
* CSV data processing for supplementary information.
* Chemical entity recognition (e.g., Chemical Name, CAS Number, Regulations) using OpenAI's GPT model.
* Data cleaning, preprocessing, and structuring into JSON format.
* Loading processed chemical data into a Neo4j graph database, creating nodes for chemicals, regulations, and their relationships.
* Streamlit-based user interface for interacting with the chemical graph data.
* Graph-based Retrieval Augmented Generation (RAG) for querying and information retrieval.
* Integration with Neo4j Aura for a cloud-hosted graph database.

## Project Structure
* `app.py`: Main application script for the Streamlit frontend.
* `data/`: Contains raw and processed data.
    * `data/raw/`: Input folder for raw PDF and CSV files.
    * `data/processed/uploaded/`: Stores processed JSON files (e.g., `outputc.json`, `output_stockholm_filtered.json`) ready for database loading.
* `notebook/`: Contains Jupyter notebooks for experimentation and workflow development.
    * `notebook/notebook.ipynb`: Main notebook demonstrating parts of the end-to-end process, experimentation with LLMs, and data loading logic.
* `src/`: Contains Python scripts for various processing steps.
    * `src/preprocess_pdfs.py`: Script for converting PDFs in `data/raw/` to text and performing initial LLM-based entity extraction.
    * `src/preprocess_csvs.py`: Script for processing CSV files from `data/raw/`.
    * `src/load_neo4j_data.py`: Script for loading processed JSON data into the Neo4j database.
* `requirements.txt`: Lists Python package dependencies.
* `.env`: Environment variable configuration file (stores API keys, database credentials). **Note: This file is not committed to the repository and should be created locally.**

## Setup and Installation
1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd CURA
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # On Windows, use: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
    * Create a file named `.env` in the root directory of the project.
    * Add the following environment variables to your `.env` file, replacing the placeholder values with your actual credentials:
        ```env
        OPENAI_API_KEY="your_openai_api_key"
        NEO4J_URI="your_neo4j_aura_uri"
        NEO4J_USER="your_neo4j_username"
        NEO4J_PASSWORD="your_neo4j_password"
        ```

## Usage

### 1. Data Ingestion and Preprocessing
* **Place your raw PDF and/or CSV files into the `data/raw/` directory.**
* **Preprocessing PDFs & LLM Extraction:**
    * Run the script:
        ```bash
        python src/preprocess_pdfs.py
        ```
    * This script will detect all PDF files in `data/raw/`, extract text, use the OpenAI API for entity recognition, and save the structured output as JSON in `data/processed/uploaded/`.
* **Preprocessing CSVs:**
    * Run the script:
        ```bash
        python src/preprocess_csvs.py
        ```
    * This script will detect all CSV files in `data/raw/`, process them, and save the output (e.g., as JSON) in `data/processed/uploaded/`.

### 2. Loading Data into Neo4j
* Ensure your `.env` file is correctly configured with your Neo4j Aura instance details.
* Run the script:
    ```bash
    python src/load_neo4j_data.py
    ```
* This will load the processed JSON data from `data/processed/uploaded/` (e.g., `outputc.json`, `output_stockholm_filtered.json`) into your Neo4j Aura graph database.

### 3. Accessing User Interfaces
* **Streamlit Frontend:**
    * Run the application:
        ```bash
        streamlit run app.py
        ```
    * This will start a local web server. Open the URL provided in your terminal (usually `http://localhost:8501`) in your web browser to access the UI.
* **Neo4j Aura Instance:**
    * Access your Neo4j Aura instance directly through the Neo4j Aura console or Neo4j Browser. This allows for direct Cypher querying, graph exploration, and administration.

## License
This project is licensed under the GNU General Public License v3.0.
You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
