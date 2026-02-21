import { useRef, useState } from "react";
import { uploadChat } from "../api/client";

/**
 * Drag-and-drop file upload panel for WhatsApp .txt exports.
 *
 * Accepts files via drag-and-drop or a hidden file input. Validates that the
 * selected file has a .txt extension before uploading. Displays a live progress
 * bar and percentage during the upload, and shows an inline error on failure.
 *
 * @param {Object}   props
 * @param {Function} props.onResult - Callback invoked with the backend response on success.
 * @returns {JSX.Element} The upload drop zone with progress and error states.
 */
export default function UploadPanel({ onResult }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  /**
   * Validate and upload a file to the backend pipeline.
   *
   * Rejects non-.txt files immediately. On success, forwards the parsed
   * result to the parent via onResult. On failure, surfaces the backend
   * error detail or a generic fallback message.
   *
   * @param {File} file - The file selected by the user.
   */
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

  /**
   * Handle a file dropped onto the drop zone.
   * Prevents default browser behaviour (opening the file) and delegates to handleFile.
   *
   * @param {DragEvent} e - The drop event from the drag-and-drop interaction.
   */
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
          /* #6 — use #16a34a (same green as ExportButton) instead of #25d366 */
          border: `2px dashed ${dragging ? "#16a34a" : "#ccc"}`,
          borderRadius: 12,
          padding: "48px 24px",
          textAlign: "center",
          cursor: loading ? "not-allowed" : "pointer",
          background: dragging ? "#f0fff4" : "#f9fafb",
          transition: "all 0.2s",
        }}
      >
        <p style={{ fontSize: 40, margin: 0 }}>📄</p>
        {/* #9 — explicit fontSize so it doesn't fall back to unpredictable browser default */}
        <p style={{ fontWeight: 600, fontSize: 16, margin: "8px 0 4px" }}>
          {loading ? `Processing… ${progress}%` : "Drop your WhatsApp chat export here"}
        </p>
        <p style={{ color: "#888", fontSize: 14 }}>
          or click to browse — .txt files only
        </p>
        {/* #10 — visual progress bar during upload */}
        {loading && (
          <div style={{ marginTop: 16, background: "#e5e7eb", borderRadius: 4, height: 4 }}>
            <div
              style={{
                width: `${progress}%`,
                background: "#16a34a",
                height: "100%",
                borderRadius: 4,
                transition: "width 0.3s",
              }}
            />
          </div>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".txt"
        style={{ display: "none" }}
        onChange={(e) => handleFile(e.target.files[0])}
      />

      {/* #4 — standardized error color from bare "red" to #dc2626 */}
      {error && (
        <p style={{ color: "#dc2626", marginTop: 12, textAlign: "center" }}>{error}</p>
      )}
    </div>
  );
}
