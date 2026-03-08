import { useState } from "react";
import SubmitReview from "./components/SubmitReview";
import ResponsePanel from "./components/ResponsePanel";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function postJson(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Request failed (${response.status}): ${errorText}`);
  }

  return response.json();
}

async function getJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Request failed (${response.status}): ${errorText}`);
  }
  return response.json();
}

export default function App() {
  const [reviewId, setReviewId] = useState(null);
  const [reviewText, setReviewText] = useState("");
  const [responseText, setResponseText] = useState("");
  const [version, setVersion] = useState(null);
  const [responseHistory, setResponseHistory] = useState([]);
  const [approved, setApproved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleGenerate = async ({ reviewText: text, tone }) => {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const reviewData = await postJson("/review", {
        review_text: text,
        tone,
      });

      const generated = await postJson(`/generate-response/${reviewData.review_id}`, {});
      const history = await getJson(`/responses/${reviewData.review_id}`);
      const newestFirstHistory = [...history].sort((a, b) => b.version - a.version);

      setReviewId(reviewData.review_id);
      setReviewText(text);
      setResponseText(generated.response_text);
      setVersion(generated.version);
      setResponseHistory(newestFirstHistory);
      setApproved(false);
      setMessage("Response generated.");
    } catch (err) {
      setError(err.message || "Failed to generate response.");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!reviewId) return;
    setLoading(true);
    setError("");
    setMessage("");

    try {
      await postJson("/approve-response", { review_id: reviewId });
      setApproved(true);
      setMessage("Response approved successfully.");
    } catch (err) {
      setError(err.message || "Failed to approve response.");
    } finally {
      setLoading(false);
    }
  };

  const handleRequestRevision = async (notes) => {
    if (!reviewId) return;
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const revised = await postJson("/request-revision", {
        review_id: reviewId,
        notes,
      });
      const history = await getJson(`/responses/${reviewId}`);
      const newestFirstHistory = [...history].sort((a, b) => b.version - a.version);

      setResponseText(revised.response_text);
      setVersion(revised.version);
      setResponseHistory(newestFirstHistory);
      setApproved(false);
      setMessage(`Revision generated (version ${revised.version}).`);
    } catch (err) {
      setError(err.message || "Failed to request revision.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <h1>AI Review Assistant</h1>
      <p>Minimal UI for review submission, response generation, revision loop, and approval.</p>

      {error ? <p className="error">{error}</p> : null}
      {message ? <p className="success">{message}</p> : null}

      <SubmitReview onGenerate={handleGenerate} loading={loading} />

      <ResponsePanel
        reviewText={reviewText}
        responseText={responseText}
        version={version}
        approved={approved}
        loading={loading}
        responseHistory={responseHistory}
        onApprove={handleApprove}
        onRequestRevision={handleRequestRevision}
      />
    </main>
  );
}
