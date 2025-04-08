import os
from typing import List, Dict
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
import json
import logging
import re

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
            # Initialize both indexes
            self.parts_index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
            self.repair_index = pc.Index(os.getenv("PINECONE_REPAIR_INDEX_NAME"))
            logger.info("Pinecone indexes initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone indexes: {str(e)}")
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
    
    def search_parts(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant parts using Pinecone."""
        try:
            logger.info(f"Searching for parts matching query: {query}")
            
            # Check for PartSelect part number (PS followed by digits)
            ps_part_match = re.search(r'PS\d+', query)
            # Check for manufacturer part number (typically alphanumeric)
            mfg_part_match = re.search(r'\b[A-Z0-9]{5,}\b', query)
            
            if ps_part_match or mfg_part_match:
                # Build filter for exact part number matches
                filter_conditions = {}
                
                if ps_part_match:
                    ps_part_number = ps_part_match.group(0)
                    logger.info(f"Detected PartSelect part number: {ps_part_number}")
                    filter_conditions["part_select_number"] = {"$eq": ps_part_number}
                
                if mfg_part_match:
                    mfg_part_number = mfg_part_match.group(0)
                    logger.info(f"Detected manufacturer part number: {mfg_part_number}")
                    # If we already have a PS part number filter, use OR condition
                    if "part_select_number" in filter_conditions:
                        filter_conditions = {
                            "$or": [
                                {"part_select_number": {"$eq": ps_part_number}},
                                {"manufacturer_part_number": {"$eq": mfg_part_number}}
                            ]
                        }
                    else:
                        filter_conditions["manufacturer_part_number"] = {"$eq": mfg_part_number}
                
                # Use metadata filtering to find exact part number matches
                results = self.parts_index.query(
                    vector=self.get_embedding(query),
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter_conditions
                )
                
                # If no exact matches found, try a broader search
                if not results.matches:
                    logger.info(f"No exact matches found for part numbers, trying broader search")
                    results = self.parts_index.query(
                        vector=self.get_embedding(query),
                        top_k=top_k,
                        include_metadata=True
                    )
            else:
                # Regular semantic search for non-part number queries
                results = self.parts_index.query(
                    vector=self.get_embedding(query),
                    top_k=top_k,
                    include_metadata=True
                )
            
            logger.info(f"Found {len(results.matches)} matching parts")
            return [match.metadata for match in results.matches]
        except Exception as e:
            logger.error(f"Failed to search parts: {str(e)}")
            raise

    def search_repairs(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant repair information using Pinecone."""
        try:
            logger.info(f"Searching for repair information matching query: {query}")
            query_embedding = self.get_embedding(query)
            
            results = self.repair_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            logger.info(f"Found {len(results.matches)} matching repair items")
            return [match.metadata for match in results.matches]
        except Exception as e:
            logger.error(f"Failed to search repairs: {str(e)}")
            raise

    def format_parts_context(self, parts: List[Dict]) -> str:
        """Format parts information for LLM context."""
        try:
            logger.debug("Formatting context from parts")
            context = "Relevant Parts Information:\n\n"
            
            for i, part in enumerate(parts, 1):
                try:
                    # Only include parts for refrigerators and dishwashers
                    if part['category'] not in ['Refrigerator', 'Dishwasher']:
                        continue
                        
                    context += f"Part {i}:\n"
                    context += f"• Name: {part['title']}\n"
                    context += f"• Category: {part['category']}\n"
                    context += f"• Brand: {part['brand']}\n"
                    context += f"• Part Number: {part['part_select_number']}\n"
                    if part.get('manufacturer_part_number'):
                        context += f"• Manufacturer Part Number: {part['manufacturer_part_number']}\n"
                    context += f"• Price: {part['price']}\n"
                    context += f"• Description: {part['description']}\n"
                    context += f"• Troubleshooting: {part['troubleshooting']}\n"
                    context += f"• Compatible Models: {part['compatible_models']}\n"
                    if part['installation_video_url']:
                        context += f"• Installation Guide Available\n"
                    context += "\n"
                except KeyError as e:
                    logger.warning(f"Missing field {e} in part data: {part}")
                    continue
            
            return context
        except Exception as e:
            logger.error(f"Failed to format parts context: {str(e)}")
            raise

    def format_repair_context(self, repairs: List[Dict], query: str) -> str:
        """Format repair information for LLM context."""
        try:
            logger.debug("Formatting context from repair data")
            context = "Repair Information:\n\n"
            
            # Add appliance type context
            appliance_type = "refrigerator" if "fridge" in query.lower() or "refrigerator" in query.lower() else "dishwasher"
            
            # Add overview information
            if appliance_type == "refrigerator":
                context += "Refrigerator Overview:\n"
                context += "• Most refrigerator repairs are rated as 'Easy' by 75% of our customers\n"
                context += "• Average repair time is under 20 minutes with basic tools\n\n"
            else:
                context += "Dishwasher Overview:\n"
                context += "• 80% of dishwasher repairs are rated as 'Easy' by our customers\n"
                context += "• Average repair time is under 15 minutes\n\n"

            # Add relevant symptoms and solutions
            context += "Common Symptoms and Solutions:\n"
            for repair in repairs:
                if "symptom" in repair:
                    context += f"• {repair['symptom']}\n"
                    context += f"  - {repair['description']}\n"
                    if "reported_by" in repair:
                        context += f"  - Reported by {repair['reported_by']}\n"
                    context += "\n"

            # Add troubleshooting videos if available
            if any("video" in str(repair).lower() for repair in repairs):
                context += "Helpful Troubleshooting Videos:\n"
                for repair in repairs:
                    if "video" in str(repair).lower():
                        context += f"• {repair.get('title', 'Troubleshooting Guide')}\n"

            return context
        except Exception as e:
            logger.error(f"Failed to format repair context: {str(e)}")
            raise

    def get_llm_response(self, query: str, parts_context: str, repair_context: str) -> str:
        """Get customer service oriented response from DeepSeek LLM."""
        try:
            logger.info("Generating LLM response")
            prompt = f"""You are a helpful appliance repair support assistant for PartSelect.

REQUIRED RESPONSE FORMAT:
Hi! [Part number or part details if applicable]:
- [First instruction]
- [Second instruction]
- [Third instruction if needed]
- [Fourth instruction if needed]
- [Fifth instruction if needed]

Let me know if you need more help!

RULES:
1. Use EXACTLY this format
2. No analysis or context before or after the response
3. No explanation of your thinking
4. No additional text besides the exact format above
5. Always start bullet points on a new line
6. Always include the greeting and closing line
7. Keep instructions clear and direct
8. Always address the user directly using "you" and "your"
9. Focus only on refrigerators and dishwashers
10. If the user provides both a PartSelect part number and a manufacturer part number, mention both in your response

Parts Information:
{parts_context}

Repair Information:
{repair_context}

Customer Question: {query}

IMPORTANT: Return ONLY the response in the exact format above. Any deviation will be rejected."""

            completion = self.deepseek_client.chat.completions.create(
                model="deepseek-ai/deepseek-r1",
                messages=[
                    {"role": "system", "content": "You are a concise appliance repair support assistant for PartSelect, focusing only on refrigerator and dishwasher repairs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                top_p=0.9,
                max_tokens=4096,
                stream=False
            )
            
            response = completion.choices[0].message.content.strip()
            
            # Remove any text that appears to be thought process or analysis
            lines = response.split('\n')
            cleaned_lines = []
            for line in lines:
                # Skip lines that look like thought process
                if any(skip in line.lower() for skip in [
                    "okay", "let me", "first", "need to", "check", "verify",
                    "looking at", "analyzing", "thinking", "considering",
                    "let's", "i need", "i will", "i should", "i must"
                ]):
                    continue
                cleaned_lines.append(line)
            
            response = "\n".join(cleaned_lines)
            
            logger.info("Successfully generated LLM response")
            return response
        except Exception as e:
            logger.error(f"DeepSeek API error: {str(e)}")
            return self.format_fallback_response(query, parts_context, repair_context)
    
    def format_fallback_response(self, query: str, parts_context: str, repair_context: str) -> str:
        """Format a polite fallback response when the LLM API fails."""
        logger.warning("Using fallback response due to LLM API failure")
        return f"""Hello! Thank you for contacting PartSelect support.

{repair_context}

{parts_context}

Let me know if you need any clarification or have additional questions."""
    
    def process_query(self, query: str) -> Dict:
        """Process a user query and return a comprehensive response with either repair guidance with replacement options or only part information depending on the query."""
        logger.info(f"Processing query: {query}")
        try:
            # Search for relevant parts
            relevant_parts = self.search_parts(query)
            
            # Search for relevant repair information
            relevant_repairs = self.search_repairs(query)
            
            # Format contexts for LLM
            parts_context = self.format_parts_context(relevant_parts)
            repair_context = self.format_repair_context(relevant_repairs, query)
            
            # Get LLM response
            response = self.get_llm_response(query, parts_context, repair_context)
            
            return {
                "response": response,
                "relevant_parts": relevant_parts
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise