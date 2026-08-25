const LABELS = {
  worth_it: { text: "Worth it", icon: "✅" },
  depends: { text: "Depends", icon: "🤔" },
  skip: { text: "Skip", icon: "❌" },
};

// Compact pill for the book-grid card. Renders nothing if there's no
// verdict yet (shouldn't happen for a 'ready' book, but be defensive).
export function VerdictPill({ label }) {
  const info = LABELS[label];
  if (!info) return null;
  return (
    <span className={`verdict-pill verdict-${label}`}>
      {info.icon} {info.text}
    </span>
  );
}

// Full callout for the book detail page: label + the model's reasoning.
export function VerdictCallout({ label, reason }) {
  const info = LABELS[label];
  if (!info) return null;
  return (
    <div className={`verdict-callout verdict-${label}`}>
      <span className="verdict-callout-label">
        {info.icon} {info.text}
      </span>
      {reason && <p>{reason}</p>}
    </div>
  );
}
