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
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 6 }}>
      {/* #2 — disabled state handled by .btn-primary:disabled in index.css */}
      {/* #5 — font size and padding now consistent with "Upload another" via .btn */}
      {/* #7 — hover handled by .btn-primary:hover:not(:disabled) in index.css */}
      <button
        onClick={handleExport}
        disabled={loading || !sales || sales.length === 0}
        className="btn btn-primary"
      >
        {loading ? "Exporting…" : "Export to Excel"}
      </button>
      {/* #4 — standardized error color from bare "red" to #dc2626 */}
      {error && <span style={{ color: "#dc2626", fontSize: 13 }}>{error}</span>}
    </div>
  );
}
