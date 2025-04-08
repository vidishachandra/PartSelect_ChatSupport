from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from query_handler import QueryHandler
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="PartSelect Support API",
    description="API for PartSelect product support chat experience",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize query handler
query_handler = QueryHandler()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    relevant_parts: list

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query about PartSelect products.
    
    Example queries:
    - "How to install part PS11752778?"
    - "Is this part compatible with model WDT780SAEM1?"
    - "My Whirlpool dishwasher is leaking. What should I do?"
    """
    try:
        result = query_handler.process_query(request.query)
        return QueryResponse(
            response=result["response"],
            relevant_parts=result["relevant_parts"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("DEBUG_MODE", "True").lower() == "true"
    ) 