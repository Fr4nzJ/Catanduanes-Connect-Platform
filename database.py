import logging
from contextlib import contextmanager
from neo4j import GraphDatabase, Driver
from flask import current_app, g
from typing import Optional, Dict, Any, List
import json

logger = logging.getLogger(__name__)

class Neo4jConnection:
    """Neo4j connection manager with session pooling and auto-reconnect"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = 'neo4j'):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = None
        self.connect()
        
    def connect(self):
        """Establish connection to Neo4j"""
        try:
            if self.driver:
                try:
                    self.driver.close()
                except:
                    pass
            
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password),
                max_connection_lifetime=30*60,  # 30 min
                keep_alive=True
            )
            # Verify connection
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        
    def ensure_connection(self):
        """Ensure driver is connected, reconnect if needed"""
        try:
            if not self.driver:
                self.connect()
                return
            
            # Test if connection is alive
            self.driver.verify_connectivity()
        except Exception as e:
            logger.warning(f"Lost connection to Neo4j, attempting to reconnect: {e}")
            self.connect()
    
    def close(self):
        """Close the driver connection"""
        if self.driver:
            try:
                self.driver.close()
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {e}")
            finally:
                self.driver = None
            
    @contextmanager
    def session(self):
        """Context manager for Neo4j sessions with auto-reconnect"""
        self.ensure_connection()
        session = None
        try:
            session = self.driver.session(database=self.database)
            yield session
        except Exception as e:
            logger.error(f"Neo4j session error: {e}")
            # If it's a connection error, try to reconnect
            if "Driver closed" in str(e):
                self.connect()
                # Retry once after reconnecting
                session = self.driver.session(database=self.database)
                yield session
            else:
                raise
        finally:
            if session:
                session.close()

def get_neo4j_db() -> Neo4jConnection:
    """Get or create Neo4j database connection"""
    if 'neo4j_db' not in g:
        g.neo4j_db = Neo4jConnection(
            current_app.config['NEO4J_URI'],
            current_app.config['NEO4J_USER'],
            current_app.config['NEO4J_PASSWORD'],
            current_app.config['NEO4J_DATABASE']
        )
    return g.neo4j_db

def init_neo4j(app):
    """Attach driver to app and verify configuration once."""
    with app.app_context():
        # 1. store driver on app (same as you do in get_neo4j_db)
        if 'neo4j_db' not in g:
            g.neo4j_db = Neo4jConnection(
                app.config['NEO4J_URI'],
                app.config['NEO4J_USER'],
                app.config['NEO4J_PASSWORD'],
                app.config['NEO4J_DATABASE']
            )
        # 2. test the connection
        g.neo4j_db.ensure_connection()
        logger.info("Successfully initialized Neo4j connection")

    @app.teardown_appcontext
    def close_neo4j(error):
        db = g.pop('neo4j_db', None)
        if db is not None:
            db.close()

def get_neo4j_db() -> Neo4jConnection:
    """Get Neo4j database connection"""
    if 'neo4j_db' not in g:
        g.neo4j_db = Neo4jConnection(
            current_app.config['NEO4J_URI'],
            current_app.config['NEO4J_USER'],
            current_app.config['NEO4J_PASSWORD'],
            current_app.config['NEO4J_DATABASE']
    )
    return g.neo4j_db

def _record_to_dict(record) -> Optional[Dict[str, Any]]:
    """Convert Neo4j record to dictionary"""
    if not record:
        return None
    return dict(record)

def _node_to_dict(node) -> Optional[Dict[str, Any]]:
    """Convert Neo4j node to dictionary"""
    if not node:
        return None
    result = dict(node)
    # IMPORTANT: Use the 'id' property from the node data, NOT node.id (which is Neo4j's internal ID)
    # Only set node.id if the 'id' property doesn't already exist in the node data
    if 'id' not in result:
        result['id'] = node.id
    result['labels'] = list(node.labels)
    return result

def safe_run(session, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Safely execute Neo4j query with error handling"""
    try:
        result = session.run(query, params or {})
        return [_record_to_dict(record) for record in result]
    except Exception as e:
        logger.error(f"Neo4j query error: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise

def create_constraints():
    """Create Neo4j constraints for data integrity"""
    db = get_neo4j_db()
    constraints = [
        "CREATE CONSTRAINT user_email_unique IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE",
        "CREATE CONSTRAINT business_name_unique IF NOT EXISTS FOR (b:Business) REQUIRE b.name IS UNIQUE",
        "CREATE CONSTRAINT job_id_unique IF NOT EXISTS FOR (j:Job) REQUIRE j.id IS UNIQUE",
        "CREATE CONSTRAINT service_id_unique IF NOT EXISTS FOR (s:Service) REQUIRE s.id IS UNIQUE",
    ]
    
    with db.session() as session:
        for constraint in constraints:
            try:
                session.run(constraint)
            except Exception as e:
                logger.warning(f"Constraint creation failed (may already exist): {e}")

def init_db():
    """Initialize database with constraints and indexes"""
    create_constraints()