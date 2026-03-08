import { useState } from "react";

export default function ResponsePanel({
  reviewText,
  responseText,
  version,
  responseHistory,
  approved,
  loading,
  onApprove,
  onRequestRevision,
}) {
  const [notes, setNotes] = useState("");
  const [showRevisionInput, setShowRevisionInput] = useState(false);
  const [copiedLabel, setCopiedLabel] = useState("");

  const handleCopy = async (text, label) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedLabel(label);
      setTimeout(() => setCopiedLabel(""), 1500);
    } catch {
      setCopiedLabel("Copy failed");
      setTimeout(() => setCopiedLabel(""), 1500);
    }
  };

  const handleRevision = async () => {
    if (!notes.trim()) {
      return;
    }
    await onRequestRevision(notes.trim());
    setNotes("");
    setShowRevisionInput(false);
  };

  return (
    <section>
      <h2>Response Panel</h2>
      {!responseText ? (
        <p>No AI response yet. Submit a review to generate one.</p>
      ) : (
        <>
          <p>
            <strong>Original Review:</strong> {reviewText}
          </p>

          <div className="latest-card">
            <div className="latest-header">
              <strong>Latest AI Response (Version {version})</strong>
              <button
                type="button"
                className="copy-inline"
                onClick={() => handleCopy(responseText, `Copied latest (v${version})`)}
              >
                Copy
              </button>
            </div>
            <p>{responseText}</p>

            {approved ? (
              <p className="success">Response approved.</p>
            ) : (
              <div className="actions">
                <button type="button" onClick={onApprove} disabled={loading}>
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => setShowRevisionInput((value) => !value)}
                  disabled={loading}
                >
                  Request Revision
                </button>
              </div>
            )}

            {showRevisionInput && !approved ? (
              <div className="revision-box">
                <label htmlFor="revision-notes">Revision Notes</label>
                <textarea
                  id="revision-notes"
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  rows={3}
                  placeholder="Make the response shorter and more friendly."
                  disabled={loading}
                />
                <button type="button" onClick={handleRevision} disabled={loading || !notes.trim()}>
                  Submit Revision Request
                </button>
              </div>
            ) : null}
          </div>

          {copiedLabel ? <p className="copy-msg">{copiedLabel}</p> : null}

          {responseHistory && responseHistory.length > 0 ? (
            <div className="history">
              <h3>Version History (Latest First)</h3>
              {responseHistory.map((item) => (
                <div key={item.response_id} className="history-item">
                  <p>
                    <strong>Version {item.version}:</strong> {item.response_text}
                  </p>
                  {item.revision_notes ? (
                    <p>
                      <strong>Revision Notes:</strong> {item.revision_notes}
                    </p>
                  ) : null}
                  <button
                    type="button"
                    className="copy-inline"
                    onClick={() => handleCopy(item.response_text, `Copied version ${item.version}`)}
                  >
                    Copy Version {item.version}
                  </button>
                </div>
              ))}
            </div>
          ) : null}

        </>
      )}
    </section>
  );
}
