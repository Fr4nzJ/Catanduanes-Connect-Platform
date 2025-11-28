import os
from database import Neo4jConnection
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test Neo4j database connection"""
    try:
        # Get connection details from environment
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        user = os.getenv('NEO4J_USERNAME', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', '00000000')
        
        # Log connection details (excluding password)
        logger.info(f"Attempting to connect to Neo4j at {uri} with user {user}...")
        
        # Create connection
        db = Neo4jConnection(
            uri=uri,
            user=user,
            password=password
        )
        
        # Try to open a session and run a simple query
        with db.session() as session:
            logger.info("Connected successfully! Testing query...")
            result = session.run("RETURN 1 as num")
            record = result.single()
            if record:
                logger.info(f"Query successful! Result: {record['num']}")
            else:
                logger.error("Query returned no results")
                
        logger.info("Connection test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()