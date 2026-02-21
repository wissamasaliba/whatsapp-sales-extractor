import { useState } from "react";
import { exportToExcel } from "../api/client";

export default function ExportButton({ sales }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleExport() {
    if (!sales || sales.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      await exportToExcel(sales);
    } catch {
      setError("Export failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
      <button
        onClick={handleExport}
        disabled={loading || !sales || sales.length === 0}
        style={{
          background: loading ? "#6b7280" : "#16a34a",
          color: "#fff",
          border: "none",
          borderRadius: 8,
          padding: "10px 24px",
          fontSize: 15,
          fontWeight: 600,
          cursor: loading || !sales?.length ? "not-allowed" : "pointer",
          transition: "background 0.2s",
        }}
      >
        {loading ? "Exporting…" : "Export to Excel"}
      </button>
      {error && <span style={{ color: "red", fontSize: 13 }}>{error}</span>}
    </div>
  );
}
