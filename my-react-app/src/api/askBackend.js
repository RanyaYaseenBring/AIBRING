const API_URL = import.meta.env.VITE_API_URL;
export async function askBackend(topic, question, sessionId) {

  const response = await fetch(
    `${API_URL}/ask`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        topic: topic,
        question: question,
        session_id: sessionId
      }),
    }
  );

  return await response.json();
}