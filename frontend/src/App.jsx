import { useState } from "react";
import Navbar from "./components/Navbar";
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
      <Navbar />

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
                {/* #5 — matches ExportButton size via shared .btn class */}
                <button onClick={handleReset} className="btn btn-secondary">
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
