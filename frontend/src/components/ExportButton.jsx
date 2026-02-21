import { useState } from "react";
import { exportToExcel } from "../api/client";

/**
 * Button that triggers an Excel export of the current sales data.
 *
 * Calls POST /export via the API client, which returns a binary .xlsx blob
 * that is automatically downloaded by the browser. The button is disabled
 * and visually muted when no sales data is available or while exporting.
 *
 * @param {Object}   props
 * @param {Object[]} props.sales - Array of sale dicts to export. Button is disabled when empty.
 * @returns {JSX.Element} A primary button with an inline error message on failure.
 */
export default function ExportButton({ sales }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Initiate the Excel export. Triggers a browser file download on success.
   * Sets an inline error message on failure.
   */
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
