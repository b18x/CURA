import os
import json
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('chemical_database')


class Configuration:
    """Class to manage configuration and environment variables"""
    @staticmethod
    def load_environment():
        """Load environment variables needed for the application"""
        load_status = load_dotenv()
        if load_status is False:
            raise RuntimeError('Environment variables not loaded.')
        
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USERNAME")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        json_paths = os.getenv("JSON_OUTPUT_FOLDER")
        
        if not all([neo4j_uri, neo4j_user, neo4j_password, json_paths]):
            raise ValueError("Missing required environment variables")
            
        return {
            "neo4j_uri": neo4j_uri,
            "neo4j_auth": (neo4j_user, neo4j_password),
            "json_paths": json_paths
        }
    
    @staticmethod
    def verify_connectivity(uri, auth):
        """Verify Neo4j connectivity"""
        try:
            with GraphDatabase.driver(uri, auth=auth) as driver:
                driver.verify_connectivity()
                logger.info("Successfully connected to Neo4j database")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Neo4j database: {e}")


class ChemicalDatabase:
    """Class to manage Neo4j database operations for chemical data"""
    def __init__(self, URI, AUTH):
        self._driver = GraphDatabase.driver(URI, auth=AUTH)

    def close(self):
        """Close the database connection"""
        self._driver.close()

    def import_json(self, chemicals_data_json):
        """
        Inserts chemical data from a JSON-like structure into Neo4j.

        Args:
            chemicals_data_json (dict): A dictionary containing a "chemicals" key with a list of chemical dictionaries.
        """
        if not isinstance(chemicals_data_json, dict) or "chemicals" not in chemicals_data_json or not isinstance(chemicals_data_json["chemicals"], list):
            raise ValueError("Invalid chemicals data format. Expected a dictionary with a 'chemicals' list.")

        with self._driver.session() as session:
            for chemical in chemicals_data_json["chemicals"]:
                self._insert_chemical(session, chemical)

    @staticmethod
    def _insert_chemical(session, chemical):
        """
        Inserts a single chemical into Neo4j, handling cases with missing CAS or chemical name.

        Args:
            session (neo4j.Session): The Neo4j session.
            chemical (dict): A dictionary representing a single chemical.
        """
        chemical_name = chemical.get("chemical_name")
        cas = chemical.get("CAS")
        regulation = chemical.get("regulation")

        if not regulation:
            logger.warning(f"Skipping chemical due to missing regulation: {chemical}")
            return

        if chemical_name and cas:
            query = """
            MERGE (c:Chemical {cas: $cas})
            MERGE (cn:ChemicalName {name: $name})
            MERGE (r:Regulation {name: $regulation})
            MERGE (cn)-[:IS_NAME_OF]->(c)
            MERGE (cn)-[:IS_REGULATED]->(r)
            MERGE (c)-[:IS_REGULATED]->(r)
            """
            session.run(query, name=chemical_name, cas=cas, regulation=regulation)

        elif chemical_name:
            query = """
            MERGE (cn:ChemicalName {name: $name})
            MERGE (r:Regulation {name: $regulation})
            MERGE (cn)-[:IS_REGULATED]->(r)
            """
            session.run(query, name=chemical_name, regulation=regulation)

        elif cas:
            query = """
            MERGE (c:Chemical {cas: $cas})
            MERGE (r:Regulation {name: $regulation})
            MERGE (c)-[:IS_REGULATED]->(r)
            """
            session.run(query, cas=cas, regulation=regulation)

        else:
            logger.warning(f"Skipping chemical due to missing chemical name and CAS: {chemical}")

    def upload_data(self, chemicals_data_json):   
        """Upload chemical data to the database"""
        try:
            self.import_json(chemicals_data_json)
            logger.info("Chemicals inserted successfully.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")


class FileProcessor:
    """Class to handle file operations and processing"""
    def __init__(self, database):
        """Initialize with database dependency injected"""
        self.database = database
    
    def process_jsons(self, json_paths):
        """Process multiple JSON files and upload their data to the database"""
        try:
            for file in os.listdir(json_paths):
                if file.endswith(".json"):
                    self.process_file(os.path.join(json_paths, file))
        except Exception as e:
            logger.error(f"Error processing files: {e}")
    
    def process_file(self, file_path):
        """Process a single JSON file"""
        try:
            logger.info(f"Processing file: {file_path}")
            with open(file_path, 'r') as f:
                chemicals_data_json = json.load(f)
            
            self.database.upload_data(chemicals_data_json)
            return True
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return False


def main():
    """Main entry point for the script"""
    try:
        # Load configuration
        config = Configuration.load_environment()
        
        # Verify connectivity
        Configuration.verify_connectivity(config["neo4j_uri"], config["neo4j_auth"])
        
        # Create database connection
        db = ChemicalDatabase(config["neo4j_uri"], config["neo4j_auth"])
        
        try:
            # Create file processor and process files
            processor = FileProcessor(db)
            processor.process_jsons(config["json_paths"])
        finally:
            # Ensure database connection is closed
            db.close()
            
        logger.info("Process completed successfully")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()