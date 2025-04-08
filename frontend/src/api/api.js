const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const getAIMessage = async (userQuery) => {
  try {
    const response = await fetch(`${API_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: userQuery }),
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const data = await response.json();
    
    return {
      role: "assistant",
      content: data.response,
      relevantParts: data.relevant_parts
    };
  } catch (error) {
    console.error('Error:', error);
    return {
      role: "assistant",
      content: "I'm sorry, I encountered an error. Please try again.",
      relevantParts: []
    };
  }
};
