import { useRef, useState } from "react";
import { uploadChat } from "../api/client";

export default function UploadPanel({ onResult }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  async function handleFile(file) {
    if (!file || !file.name.endsWith(".txt")) {
      setError("Please select a WhatsApp exported .txt file.");
      return;
    }
    setError(null);
    setLoading(true);
    setProgress(0);
    try {
      const result = await uploadChat(file, setProgress);
      onResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  }

  return (
    <div style={{ maxWidth: 520, margin: "0 auto" }}>
      <div
        onClick={() => !loading && inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        style={{
          border: `2px dashed ${dragging ? "#25d366" : "#ccc"}`,
          borderRadius: 12,
          padding: "48px 24px",
          textAlign: "center",
          cursor: loading ? "not-allowed" : "pointer",
          background: dragging ? "#f0fff4" : "#fafafa",
          transition: "all 0.2s",
        }}
      >
        <p style={{ fontSize: 40, margin: 0 }}>📄</p>
        <p style={{ fontWeight: 600, margin: "8px 0 4px" }}>
          {loading ? `Processing… ${progress}%` : "Drop your WhatsApp chat export here"}
        </p>
        <p style={{ color: "#888", fontSize: 14 }}>
          or click to browse — .txt files only
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".txt"
        style={{ display: "none" }}
        onChange={(e) => handleFile(e.target.files[0])}
      />

      {error && (
        <p style={{ color: "red", marginTop: 12, textAlign: "center" }}>{error}</p>
      )}
    </div>
  );
}
