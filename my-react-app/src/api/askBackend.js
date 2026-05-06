export async function askBackend(topic, question, sessionId) {
  const response = await fetch("http://172.20.20.68:8000/ask"
, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      topic: topic,
      question: question,
      session_id: sessionId
    }),
  });

  return await response.json();
}
