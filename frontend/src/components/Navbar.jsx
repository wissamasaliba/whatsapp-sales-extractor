import logo from "../assets/logo.jpg";

/**
 * Top navigation bar displayed across the full width of every page.
 *
 * Renders the company logo and the application name on a dark background.
 * The logo uses objectFit "contain" to ensure it is never clipped.
 *
 * @returns {JSX.Element} A full-width <nav> element.
 */
export default function Navbar() {
  return (
    <nav
      style={{
        width: "100%",
        background: "#111827",
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "12px 24px",
        boxSizing: "border-box",
        boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
      }}
    >
      <img
        src={logo}
        alt="Logo"
        style={{ height: 40, width: 40, borderRadius: 8, objectFit: "contain", flexShrink: 0 }}
      />
      <span
        style={{
          color: "#f9fafb",
          fontSize: 18,
          fontWeight: 700,
          letterSpacing: "0.01em",
        }}
      >
        WhatsApp Sales Extractor
      </span>
    </nav>
  );
}
