import { useState } from "react";

// Shows the cover image if we have a URL and it actually loads; falls back
// to the 📖 placeholder both when there's no cover_url at all AND when the
// <img> fails to load at runtime (bad URL, network hiccup, host down) --
// without onError, a load failure would show a broken-image icon instead.
export default function BookCover({ src, title, large = false }) {
  const [failed, setFailed] = useState(false);
  const className = large ? "book-cover book-cover-large" : "book-cover";

  if (!src || failed) {
    return (
      <div className={className}>
        <div className="book-cover-placeholder" aria-hidden="true">
          📖
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <img
        src={src}
        alt={`Cover of ${title}`}
        loading={large ? undefined : "lazy"}
        onError={() => setFailed(true)}
      />
    </div>
  );
}
