import { useState } from "react";

const TONES = ["professional", "friendly", "apologetic"];

export default function SubmitReview({ onGenerate, loading }) {
  const [reviewText, setReviewText] = useState("");
  const [tone, setTone] = useState(TONES[0]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!reviewText.trim()) {
      return;
    }
    await onGenerate({ reviewText: reviewText.trim(), tone });
  };

  return (
    <section>
      <h2>Submit Review</h2>
      <form onSubmit={handleSubmit}>
        <label htmlFor="review-text">Review Text</label>
        <textarea
          id="review-text"
          value={reviewText}
          onChange={(event) => setReviewText(event.target.value)}
          rows={6}
          placeholder="Type the customer review here"
          disabled={loading}
        />

        <label htmlFor="tone">Tone</label>
        <select
          id="tone"
          value={tone}
          onChange={(event) => setTone(event.target.value)}
          disabled={loading}
        >
          {TONES.map((toneOption) => (
            <option key={toneOption} value={toneOption}>
              {toneOption}
            </option>
          ))}
        </select>

        <button type="submit" disabled={loading || !reviewText.trim()}>
          {loading ? "Generating..." : "Generate Response"}
        </button>
      </form>
    </section>
  );
}
