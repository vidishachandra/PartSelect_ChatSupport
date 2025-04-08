const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Log API configuration on startup
console.log('API Configuration:', {
  baseUrl: API_URL,
  environment: process.env.NODE_ENV
});

export const getAIMessage = async (userQuery) => {
  console.log('Sending query to backend:', { query: userQuery });
  
  try {
    const response = await fetch(`${API_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: userQuery }),
    });

    // Log response status
    console.log('Backend response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Backend error response:', {
        status: response.status,
        statusText: response.statusText,
        error: errorData
      });
      throw new Error(`Backend error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Backend response data:', {
      responseLength: data.response?.length,
      partsCount: data.relevant_parts?.length
    });
    
    return {
      role: "assistant",
      content: data.response,
      relevantParts: data.relevant_parts
    };
  } catch (error) {
    console.error('API call failed:', {
      error: error.message,
      stack: error.stack,
      query: userQuery
    });
    
    // Return a more informative error message
    return {
      role: "assistant",
      content: `I apologize, but I encountered an error while processing your request: ${error.message}. Please try again or contact support if the issue persists.`,
      relevantParts: [],
      error: true
    };
  }
};
