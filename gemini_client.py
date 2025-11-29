import os
import logging
from typing import List, Dict, Optional
import google.generativeai as genai

# Set up logging
logger = logging.getLogger(__name__)

SYSTEM_TEMPLATE = """You are an AI assistant for CatanduanesConnect, a platform connecting job seekers, businesses, 
and service providers in Catanduanes. Help users find jobs, businesses, and services while providing accurate,
helpful information about opportunities in the region. When discussing jobs or services, always try to include
specific details about location, requirements, and how to apply or contact.

Key Features to Remember:
• Job searching and application assistance
• Business directory and service provider lookup
• Location-based recommendations
• Professional communication tips

Please maintain a helpful, professional tone and prioritize local opportunities in Catanduanes."""

class GeminiChat:
    """Client for interacting with Google's Gemini API."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Google Gemini API key. If None, will try to get from environment.
        """
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
            
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            raise ValueError("GEMINI_API_KEY environment variable is not set")
            
        try:
            # Initialize the Gemini client
            logger.debug("Initializing Gemini client...")
            
            # Initialize the Gemini client with basic configuration
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Test the connection with a simple prompt
            try:
                response = self.model.generate_content("Hi")
                if response and hasattr(response, 'text') and response.text:
                    logger.info("Successfully initialized and tested Gemini client")
                else:
                    raise ValueError("Failed to get test response from Gemini model")
            except Exception as e:
                logger.error(f"Failed to test Gemini connection: {str(e)}")
                raise ValueError(f"Failed to test Gemini connection: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise
            
    def extract_search_params(self, message: str) -> Dict[str, str]:
        """Extract search parameters from the user's message."""
        params = {}
        
        # Look for category in the message
        category_patterns = [
            r"category[:\s]+(\w+)",
            r"in the (\w+) category",
            r"related to (\w+)",
            r"about (\w+)"
        ]
        for pattern in category_patterns:
            match = re.search(pattern, message.lower())
            if match:
                params["category"] = match.group(1)
                break

        # Look for location in the message
        location_patterns = [
            r"in\s+(\w+(?:\s+\w+)*(?:\s+City)?)",
            r"at\s+(\w+(?:\s+\w+)*(?:\s+City)?)",
            r"near\s+(\w+(?:\s+\w+)*(?:\s+City)?)",
            r"around\s+(\w+(?:\s+\w+)*(?:\s+City)?)"
        ]
        for pattern in location_patterns:
            match = re.search(pattern, message)
            if match:
                params["location"] = match.group(1)
                break
                
        # Use the rest as a general search query
        # Remove found category and location if any
        query = message
        if "category" in params:
            query = re.sub(r"category[:\s]+" + params["category"], "", query, flags=re.IGNORECASE)
        if "location" in params:
            query = re.sub(r"in\s+" + params["location"], "", query, flags=re.IGNORECASE)
            
        params["query"] = query.strip()
        return params

    def _get_relevant_data(self, message: str) -> Optional[str]:
        """Get relevant data from database based on user query."""
        try:
            # Extract search parameters from message
            params = self.extract_search_params(message)
            query = params.get("query", "")
            category = params.get("category")
            location = params.get("location")
            
            context_parts = []
            db = get_neo4j_db()
            
            with db.session() as session:
                # Search for jobs
                jobs_query = """
                MATCH (j:JobOffer)
                WHERE j.is_active = true 
                AND (toLower(j.title) CONTAINS toLower($query)
                OR toLower(j.description) CONTAINS toLower($query)
                OR toLower(j.requirements) CONTAINS toLower($query))
                """
                
                if location:
                    jobs_query += "AND toLower(j.location) CONTAINS toLower($location) "
                if category:
                    jobs_query += "AND toLower(j.category) CONTAINS toLower($category) "
                    
                jobs_query += "RETURN j LIMIT 3"
                
                jobs = session.run(jobs_query, 
                                 query=query,
                                 location=location,
                                 category=category).data()
                
                if jobs:
                    context_parts.append("Relevant Jobs:")
                    for job_data in jobs:
                        job = job_data['j']
                        context_parts.append(f"- {job.get('title')} at {job.get('company_name', 'N/A')}")
                        context_parts.append(f"  Location: {job.get('location', 'N/A')}")
                        if job.get('salary'):
                            context_parts.append(f"  Salary: ₱{job['salary']}")
                        if job.get('description'):
                            desc = job['description']
                            if len(desc) > 200:
                                desc = desc[:200] + "..."
                            context_parts.append(f"  Description: {desc}")

                # Search for services
                services_query = """
                MATCH (s:Service)
                WHERE s.is_active = true 
                AND (toLower(s.title) CONTAINS toLower($query)
                OR toLower(s.description) CONTAINS toLower($query))
                """
                
                if location:
                    services_query += "AND toLower(s.location) CONTAINS toLower($location) "
                if category:
                    services_query += "AND toLower(s.category) CONTAINS toLower($category) "
                    
                services_query += "RETURN s LIMIT 3"
                
                services = session.run(services_query,
                                     query=query,
                                     location=location,
                                     category=category).data()
                
                if services:
                    context_parts.append("\nRelevant Services:")
                    for service_data in services:
                        service = service_data['s']
                        context_parts.append(f"- {service.get('title', 'N/A')}")
                        context_parts.append(f"  Location: {service.get('location', 'N/A')}")
                        context_parts.append(f"  Category: {service.get('category', 'N/A')}")
                        if service.get('description'):
                            desc = service['description']
                            if len(desc) > 200:
                                desc = desc[:200] + "..."
                            context_parts.append(f"  Description: {desc}")

                # Search for businesses
                businesses_query = """
                MATCH (b:Business)
                WHERE b.is_active = true 
                AND (toLower(b.name) CONTAINS toLower($query)
                OR toLower(b.description) CONTAINS toLower($query))
                """
                
                if location:
                    businesses_query += "AND toLower(b.location) CONTAINS toLower($location) "
                if category:
                    businesses_query += "AND toLower(b.category) CONTAINS toLower($category) "
                    
                businesses_query += "RETURN b LIMIT 3"
                
                businesses = session.run(businesses_query,
                                       query=query,
                                       location=location,
                                       category=category).data()
                
                if businesses:
                    context_parts.append("\nRelevant Businesses:")
                    for business_data in businesses:
                        business = business_data['b']
                        context_parts.append(f"- {business.get('name', 'N/A')}")
                        context_parts.append(f"  Location: {business.get('location', 'N/A')}")
                        context_parts.append(f"  Category: {business.get('category', 'N/A')}")
                        if business.get('description'):
                            desc = business['description']
                            if len(desc) > 200:
                                desc = desc[:200] + "..."
                            context_parts.append(f"  Description: {desc}")
            
            return "\n".join(context_parts) if context_parts else None
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return None

    def send_message(self, message: str, context: str = None, history: List[Dict[str, str]] = None) -> str:
        """
        Send a message to the Gemini model and get the response.
        
        Args:
            message: The user's message
            context: Optional relevant context from the database
            history: Optional chat history as a list of role/content dicts
            
        Returns:
            The model's response text
        """
        try:
            # Build the complete prompt
            prompt = "You are the CatanduanesConnect AI assistant. "
            prompt += "Your role is to help users find jobs, businesses, and services in Catanduanes. "
            prompt += "Please be friendly and helpful.\n\n"
            
            # Add context if available
            if context:
                prompt += f"Here is some relevant information:\n{context}\n\n"
            
            # Add chat history if provided
            if history:
                for msg in history[-5:]:  # Only use last 5 messages
                    role = msg["role"].capitalize()
                    prompt += f"{role}: {msg['content']}\n"
            
            # Add current message
            prompt += f"User: {message}\nAssistant:"
            
            # Get response from model with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.7,
                            "top_p": 0.8,
                            "top_k": 40,
                            "max_output_tokens": 2048,
                        }
                    )
            
                    if response and hasattr(response, 'text') and response.text:
                        # Clean and format the response
                        formatted_response = response.text.strip()
                        formatted_response = formatted_response.replace("**", "").replace("*", "• ")
                        return formatted_response
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                        continue
                    else:
                        raise
            
            return "I apologize, but I wasn't able to generate a helpful response. Please try rephrasing your question."
            
        except Exception as e:
            logger.error(f"Error getting response from Gemini: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later."


# Global chat instance
_chat_instance = None


def get_gemini_response(prompt: str, temperature: float = 0.7) -> str:
    """
    Get a simple response from Gemini API without conversation history.
    
    Args:
        prompt: The prompt to send to Gemini
        temperature: Temperature for response generation (0.0-1.0)
    
    Returns:
        str: The response from Gemini
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
        
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()
        
        return "Unable to generate response"
        
    except Exception as e:
        logger.error(f"Error getting response from Gemini: {str(e)}")
        raise