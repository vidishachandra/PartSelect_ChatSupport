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
repair_index = pc.Index(os.getenv("PINECONE_REPAIR_INDEX_NAME"))

def get_embedding(text: str) -> List[float]:
    """Get embedding using sentence-transformers."""
    return model.encode(text).tolist()

def prepare_repair_data(repair_data: Dict, appliance_type: str) -> List[Dict]:
    """Prepare repair data for indexing."""
    prepared_data = []
    
    # Add overview
    overview = {
        "id": f"{appliance_type}_overview",
        "text": repair_data["overview"]["description"],
        "appliance": appliance_type,
        "type": "overview"
    }
    prepared_data.append(overview)
    
    # Add symptoms
    for symptom in repair_data["common_symptoms"]:
        symptom_data = {
            "id": f"{appliance_type}_{symptom['symptom'].lower().replace(' ', '_')}",
            "symptom": symptom["symptom"],
            "description": symptom["description"],
            "reported_by": symptom["reported_by"],
            "appliance": appliance_type,
            "type": "symptom"
        }
        prepared_data.append(symptom_data)
    
    # Add videos
    for video in repair_data["troubleshooting_videos"]:
        video_data = {
            "id": f"{appliance_type}_video_{len(prepared_data)}",
            "title": video["title"],
            "url": video["url"],
            "appliance": appliance_type,
            "type": "video"
        }
        prepared_data.append(video_data)
    
    return prepared_data

def index_repair_data():
    """Load repair data and index it in Pinecone."""
    print("Starting indexing process for repair data...")
    
    all_data = []
    
    # Load dishwasher repairs
    print("Loading dishwasher repair data...")
    with open('repair_data/dishwasher_repairs.json', 'r') as f:
        dishwasher_data = json.load(f)
        dishwasher_items = prepare_repair_data(dishwasher_data, "dishwasher")
        all_data.extend(dishwasher_items)
    print(f"Prepared {len(dishwasher_items)} dishwasher repair items")
    
    # Load refrigerator repairs
    print("Loading refrigerator repair data...")
    with open('repair_data/refrigerator_repairs.json', 'r') as f:
        refrigerator_data = json.load(f)
        refrigerator_items = prepare_repair_data(refrigerator_data, "refrigerator")
        all_data.extend(refrigerator_items)
    print(f"Prepared {len(refrigerator_items)} refrigerator repair items")
    
    print(f"Total items to index: {len(all_data)}")
    
    # Index data in batches
    batch_size = 50
    for i in range(0, len(all_data), batch_size):
        batch = all_data[i:i + batch_size]
        vectors = []
        
        for item in batch:
            # Create search text combining all relevant fields
            search_text = f"{item['appliance']} {item.get('type', '')} "
            if 'symptom' in item:
                search_text += f"{item['symptom']} {item['description']} "
            elif 'title' in item:
                search_text += f"{item['title']} "
            else:
                search_text += f"{item.get('text', '')}"
            
            # Get embedding for the combined text
            vector = get_embedding(search_text)
            
            # Prepare vector data
            vector_data = {
                "id": item["id"],
                "values": vector,
                "metadata": item
            }
            vectors.append(vector_data)
        
        # Upsert batch to Pinecone
        repair_index.upsert(vectors=vectors)
        print(f"Indexed {len(vectors)} items")
    
    print("Indexing complete for repair data!")

if __name__ == "__main__":
    index_repair_data() 