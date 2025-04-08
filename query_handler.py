import os
from typing import List, Dict
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Pinecone client
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

class QueryHandler:
    def __init__(self):
        logger.info("Initializing QueryHandler...")
        try:
            self.index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
            logger.info("Pinecone index initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone index: {str(e)}")
            raise

        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence transformer model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {str(e)}")
            raise

        try:
            self.deepseek_client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=os.getenv("NVIDIA_API_KEY")
            )
            logger.info("DeepSeek client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek client: {str(e)}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using sentence-transformers."""
        try:
            logger.debug(f"Generating embedding for text: {text[:100]}...")
            embedding = self.model.encode(text).tolist()
            logger.debug(f"Generated embedding of length: {len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise
    
    def search_parts(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for relevant parts using Pinecone."""
        try:
            logger.info(f"Searching for parts matching query: {query}")
            query_embedding = self.get_embedding(query)
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            logger.info(f"Found {len(results.matches)} matching parts")
            return [match.metadata for match in results.matches]
        except Exception as e:
            logger.error(f"Failed to search parts: {str(e)}")
            raise
    
    def format_context(self, parts: List[Dict]) -> str:
        """Format parts information for LLM context."""
        try:
            logger.debug("Formatting context from parts")
            context = "Here are the relevant parts information:\n\n"
            
            for i, part in enumerate(parts, 1):
                try:
                    context += f"Part {i}:\n"
                    context += f"Title: {part['title']}\n"
                    context += f"Category: {part['category']}\n"
                    context += f"Brand: {part['brand']}\n"
                    context += f"Part Number: {part['part_select_number']}\n"
                    context += f"Price: {part['price']}\n"
                    context += f"Description: {part['description']}\n"
                    context += f"Troubleshooting: {part['troubleshooting']}\n"
                    context += f"Compatible Models: {part['compatible_models']}\n"
                    if part['installation_video_url']:
                        context += f"Installation Video: {part['installation_video_url']}\n"
                    context += "\n"
                except KeyError as e:
                    logger.warning(f"Missing field {e} in part data: {part}")
                    continue
            
            return context
        except Exception as e:
            logger.error(f"Failed to format context: {str(e)}")
            raise
    
    def get_llm_response(self, query: str, context: str) -> str:
        """Get response from DeepSeek LLM using NVIDIA API."""
        try:
            logger.info("Generating LLM response")
            prompt = f"""You are a helpful product support assistant for PartSelect. 
            Use the following context to answer the user's question.
            If you're not sure about something, say so.
            
            Context:
            {context}
            
            User Question: {query}
            
            Please provide a helpful, accurate response based on the available information."""

            completion = self.deepseek_client.chat.completions.create(
                model="deepseek-ai/deepseek-r1",
                messages=[
                    {"role": "system", "content": "You are a helpful product support assistant for PartSelect."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                top_p=0.7,
                max_tokens=4096,
                stream=False
            )
            
            response = completion.choices[0].message.content
            logger.info("Successfully generated LLM response")
            return response
        except Exception as e:
            logger.error(f"DeepSeek API error: {str(e)}")
            return self.format_fallback_response(query, context)
    
    def format_fallback_response(self, query: str, context: str) -> str:
        """Format a fallback response when the LLM API fails."""
        logger.warning("Using fallback response due to LLM API failure")
        return f"""I found some relevant parts that might help with your query: "{query}".

{context}

To order any of these parts or get more information, please use the part number provided. 
Each part comes with detailed installation instructions, and some parts include video guides for installation."""
    
    def process_query(self, query: str) -> Dict:
        """Process a user query and return response with relevant parts."""
        logger.info(f"Processing query: {query}")
        try:
            # Search for relevant parts
            relevant_parts = self.search_parts(query)
            
            # Format context for LLM
            context = self.format_context(relevant_parts)
            
            # Get LLM response
            response = self.get_llm_response(query, context)
            
            logger.info("Query processed successfully")
            return {
                "response": response,
                "relevant_parts": relevant_parts
            }
        except Exception as e:
            logger.error(f"Failed to process query: {str(e)}")
            raise