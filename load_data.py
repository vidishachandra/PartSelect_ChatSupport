import json
import os
from typing import List, Dict
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')  # This model has 384 dimensions

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

def get_embedding(text: str) -> List[float]:
    """Get embedding using sentence-transformers."""
    return model.encode(text).tolist()

def create_search_text(part: Dict) -> str:
    """Create a searchable text from part metadata."""
    return f"""
    Title: {part['title']}
    Category: {part['category']}
    Brand: {part['brand']}
    Description: {part['description']}
    Part Number: {part['partSelectNumber']}
    Manufacturer Part Number: {part['manufacturerPartNumber']}
    Troubleshooting: {part['troubleShooting']}
    Compatible Models: {part['compatibleModels']}
    """

def index_parts():
    """Load parts and index them in Pinecone."""
    print("Starting indexing process...")
    
    # Load parts data from both JSON files
    all_parts = []
    
    # Load refrigerator parts
    print("Loading refrigerator parts...")
    with open('fake_refrigerator_parts.json', 'r') as f:
        refrigerator_parts = json.load(f)
        all_parts.extend(refrigerator_parts)
    print(f"Loaded {len(refrigerator_parts)} refrigerator parts")
    
    # Load dishwasher parts
    print("Loading dishwasher parts...")
    with open('fake_dishwasher_parts.json', 'r') as f:
        dishwasher_parts = json.load(f)
        all_parts.extend(dishwasher_parts)
    print(f"Loaded {len(dishwasher_parts)} dishwasher parts")
    
    print(f"Total parts to index: {len(all_parts)}")
    
    # Index each part
    for i, part in enumerate(all_parts):
        search_text = create_search_text(part)
        embedding = get_embedding(search_text)
        
        # Prepare metadata with all available fields
        metadata = {
            'title': part['title'],
            'category': part['category'],
            'brand': part['brand'],
            'part_select_number': part['partSelectNumber'],
            'manufacturer_part_number': part['manufacturerPartNumber'],
            'description': part['description'],
            'price': part['price'],
            'image_url': part['imageURL'],
            'troubleshooting': part['troubleShooting'],
            'compatible_models': part['compatibleModels'],
            'replaces': part['replaces'],
            'rating': part['rating'],
            'installation_video_url': part['installationVideoURL']
        }
        
        # Upsert to Pinecone
        index.upsert(
            vectors=[{
                'id': f"part_{i}",
                'values': embedding,
                'metadata': metadata
            }]
        )
        
        if (i + 1) % 10 == 0:
            print(f"Indexed {i + 1} parts...")
    
    print("Indexing completed!")

if __name__ == "__main__":
    index_parts() 