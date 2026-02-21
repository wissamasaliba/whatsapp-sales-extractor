import { useState } from "react";
import UploadPanel from "./components/UploadPanel";
import SalesTable from "./components/SalesTable";
import ExportButton from "./components/ExportButton";

export default function App() {
  const [result, setResult] = useState(null);

  function handleResult(data) {
    setResult(data);
  }

  function handleReset() {
    setResult(null);
  }

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", minHeight: "100vh", background: "#f9fafb" }}>
      {/* Header */}
      <header
        style={{
          background: "#25d366",
          color: "#fff",
          padding: "16px 32px",
          display: "flex",
          alignItems: "center",
          gap: 12,
          boxShadow: "0 2px 8px rgba(0,0,0,0.12)",
        }}
      >
        <span style={{ fontSize: 28 }}>💬</span>
        <div>
          <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>WhatsApp Sales Extractor</h1>
          <p style={{ margin: 0, fontSize: 13, opacity: 0.85 }}>
            Upload a chat export and extract structured sales data with AI
          </p>
        </div>
      </header>

      <main style={{ maxWidth: 1100, margin: "0 auto", padding: "40px 24px" }}>
        {!result ? (
          <UploadPanel onResult={handleResult} />
        ) : (
          <>
            {/* Toolbar */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 24,
                flexWrap: "wrap",
                gap: 12,
              }}
            >
              <div>
                <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>
                  {result.filename}
                </h2>
                {result.stats && (
                  <p style={{ margin: "4px 0 0", fontSize: 13, color: "#555" }}>
                    {result.stats.messages_parsed} messages parsed &bull;{" "}
                    {result.stats.valid_sales} sales extracted &bull;{" "}
                    {result.stats.flagged_errors} issues flagged
                  </p>
                )}
              </div>

              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <button
                  onClick={handleReset}
                  style={{
                    background: "#fff",
                    border: "1px solid #d1d5db",
                    borderRadius: 8,
                    padding: "9px 20px",
                    fontSize: 14,
                    cursor: "pointer",
                  }}
                >
                  Upload another
                </button>
                <ExportButton sales={result.sales} />
              </div>
            </div>

            <SalesTable sales={result.sales} errors={result.errors} />
          </>
        )}
      </main>
    </div>
  );
}
