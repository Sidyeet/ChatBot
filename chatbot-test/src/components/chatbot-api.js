/**
 * Chatbot API Helper Functions
 * Handles all communication with FastAPI backend
 */

const API_BASE_URL =
  (typeof process !== "undefined" && process?.env?.REACT_APP_CHATBOT_API) || "http://localhost:8001";

/**
 * Send a message to the chatbot
 */
export async function sendChatMessage(userMessage, userId = "anonymous", conversationHistory = []) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_message: userMessage,
        user_id: userId,
        conversation_history: conversationHistory,
      }),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error sending chat message:", error);
    throw error;
  }
}

/**
 * Upload a document to the knowledge base
 */
export async function uploadDocument(file, docType = "faq") {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("doc_type", docType);

    const response = await fetch(`${API_BASE_URL}/admin/upload-document`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error uploading document:", error);
    throw error;
  }
}

/**
 * Get unanswered queries for admin
 */
export async function getUnansweredQueries() {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/unanswered-queries`);

    if (!response.ok) {
      throw new Error(`Failed to fetch queries: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching unanswered queries:", error);
    throw error;
  }
}

/**
 * Admin responds to an unanswered query
 */
export async function respondToQuery(queryId, response) {
  try {
    const apiResponse = await fetch(`${API_BASE_URL}/admin/respond-query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query_id: queryId,
        response: response,
      }),
    });

    if (!apiResponse.ok) {
      throw new Error(`Failed to respond: ${apiResponse.statusText}`);
    }

    return await apiResponse.json();
  } catch (error) {
    console.error("Error responding to query:", error);
    throw error;
  }
}

/**
 * Get dashboard statistics
 */
export async function getStatistics() {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/statistics`);

    if (!response.ok) {
      throw new Error(`Failed to fetch statistics: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching statistics:", error);
    throw error;
  }
}

/**
 * Health check with retry logic for Render cold starts.
 * Render free tier spins down after inactivity and takes ~50s to wake up.
 * We retry up to 3 times with increasing delays to handle this.
 */
export async function checkHealth() {
  const maxRetries = 3;
  const retryDelayMs = 15000; // 15 seconds between retries

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 20000); // 20s timeout per attempt

      const response = await fetch(`${API_BASE_URL}/health`, {
        signal: controller.signal,
      });
      clearTimeout(timeout);

      if (!response.ok) {
        throw new Error("API is down");
      }

      return await response.json();
    } catch (error) {
      console.warn(`Health check attempt ${attempt}/${maxRetries} failed:`, error.message);
      if (attempt < maxRetries) {
        // Wait before retrying (server is likely waking up)
        await new Promise((resolve) => setTimeout(resolve, retryDelayMs));
      } else {
        console.error("Health check failed after all retries");
        throw error;
      }
    }
  }
}
