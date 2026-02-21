const COLUMNS = [
  { key: "timestamp", label: "Timestamp" },
  { key: "sender", label: "Sender" },
  { key: "product", label: "Product" },
  { key: "quantity", label: "Qty" },
  { key: "unit_price", label: "Unit Price" },
  { key: "total_price", label: "Total" },
  { key: "currency", label: "Currency" },
  { key: "notes", label: "Notes" },
];

export default function SalesTable({ sales, errors }) {
  if (!sales || sales.length === 0) {
    return <p style={{ textAlign: "center", color: "#888" }}>No sales data to display.</p>;
  }

  return (
    <div style={{ overflowX: "auto" }}>
      {errors && errors.length > 0 && (
        <details style={{ marginBottom: 16 }}>
          <summary style={{ cursor: "pointer", color: "#b45309", fontWeight: 600 }}>
            {errors.length} issue{errors.length !== 1 ? "s" : ""} flagged by auditor
          </summary>
          <ul style={{ fontSize: 13, color: "#92400e" }}>
            {errors.map((e, i) => (
              <li key={i}>{e.reason}</li>
            ))}
          </ul>
        </details>
      )}

      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
        <thead>
          {/* #3 — aligned to Navbar color (#111827) instead of unrelated navy #1f4e79 */}
          <tr style={{ background: "#111827", color: "#fff" }}>
            {COLUMNS.map((c) => (
              <th
                key={c.key}
                style={{ padding: "10px 12px", textAlign: "left", whiteSpace: "nowrap" }}
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sales.map((row, i) => (
            <tr
              key={i}
              style={{ background: i % 2 === 0 ? "#fff" : "#f5f5f5" }}
            >
              {COLUMNS.map((c) => (
                <td key={c.key} style={{ padding: "8px 12px", borderBottom: "1px solid #e5e7eb" }}>
                  {row[c.key] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <p style={{ color: "#555", fontSize: 13, marginTop: 8 }}>
        {sales.length} sale{sales.length !== 1 ? "s" : ""} found
      </p>
    </div>
  );
}
