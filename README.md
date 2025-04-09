# Instalily Case Study - Appliance Support Assistant

A smart chatbot application that provides installation and repair guidance for appliance parts, specifically focused on refrigerators and dishwashers. The application uses Retrieval-Augmented Generation (RAG) to provide accurate, context-aware responses based on a comprehensive parts and repair database.

## Features

- **Intelligent Part Search**: Automatically identifies and searches for relevant parts based on user queries
- **Installation Guidance**: Provides step-by-step installation instructions for specific parts
- **Repair Troubleshooting**: Offers diagnostic steps and solutions for common appliance issues
- **Part Compatibility**: Checks and displays compatible parts with manufacturer model numbers
- **Interactive UI**: Clean, modern interface with real-time responses and loading states
- **Product Cards**: Displays relevant parts with images, prices, and installation video links
- **RAG Implementation**: Uses vector embeddings and semantic search to retrieve relevant context for accurate responses

## Tech Stack

### Backend
- Python 3.x
- FastAPI
- Pinecone (Vector Database for RAG)
- Sentence Transformers (for text embeddings)
- DeepSeek LLM (for response generation)
- RAG Architecture:
  - Vector embeddings for semantic search
  - Context retrieval from parts and repair databases
  - Augmented prompt generation with retrieved context
  - Structured response formatting

### Frontend
- React
- Marked (Markdown rendering)
- CSS Modules

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd Instalily_casestudy
```

2. Install backend dependencies:
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```
PINECONE_API_KEY=your_pinecone_api_key
NVIDIA_API_KEY=your_nvidia_api_key
PINECONE_INDEX_NAME=your_parts_index_name
PINECONE_REPAIR_INDEX_NAME=your_repair_index_name
```

## Running the Application

1. Start the backend server:
```bash
python main.py
```

2. Start the frontend development server:
```bash
cd frontend
npm start
```

The application will be available at `http://localhost:3000`

## Usage

1. Type your question in the chat input. Example queries:
   - "How to install part PS67910065?"
   - "My Whirlpool dishwasher is leaking. What should I do?"
   - "Is this part compatible with manufacturer model WDT780SAEM1?"

2. The assistant will respond with:
   - Installation steps for specific parts
   - Troubleshooting guidance for repair issues
   - Relevant part recommendations with prices and video links

## Response Format

The assistant follows a strict response format:
```
Hi! [Part number or part details if applicable]:
- [First instruction]
- [Second instruction]
- [Third instruction if needed]

Let me know if you need more help!
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
