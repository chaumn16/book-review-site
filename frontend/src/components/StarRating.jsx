// Read-only average-rating display, e.g. "★★★★☆ 4.2 (12)". Renders nothing
// when there are no ratings yet, so callers can drop it in unconditionally.
export default function StarRating({ average, count }) {
  if (!count) return null;

  const rounded = Math.round(average);
  const stars = "★".repeat(rounded) + "☆".repeat(5 - rounded);

  return (
    <span className="star-rating" title={`${average} out of 5 (${count} rating${count === 1 ? "" : "s"})`}>
      <span className="star-rating-stars" aria-hidden="true">
        {stars}
      </span>
      <span className="star-rating-text">
        {average} ({count})
      </span>
    </span>
  );
}
