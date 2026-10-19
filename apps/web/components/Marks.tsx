const MARK_COLORS = ["#097fe8", "#f64932", "#ffb110", "#62aef0"] as const;

export function AvatarMark({ color, variant }: { color: string; variant: number }) {
  const content =
    variant % 4 === 0 ? (
      <g fill="none" stroke="#111" strokeWidth="2.5" strokeLinecap="round">
        <circle cx="16" cy="13" r="2.5" fill="#111" stroke="none" />
        <circle cx="26" cy="13" r="2.5" fill="#111" stroke="none" />
        <path d="M13 22c2 3.4 4.2 5 7 5s5-1.6 7-5" />
      </g>
    ) : variant % 4 === 1 ? (
      <g fill="#111">
        <path d="M21 11c4 0 7 2.6 7 6 0 3-2.2 4.6-4.6 5.4l1.8 4.4c-2-1-3.4-2-5-2-2.8 0-6.2-2-6.2-5.4 0-4 3-8.4 7-8.4Z" />
      </g>
    ) : variant % 4 === 2 ? (
      <g fill="none" stroke="#111" strokeWidth="2.5" strokeLinecap="round">
        <circle cx="16" cy="14" r="2.2" fill="#111" stroke="none" />
        <circle cx="26" cy="14" r="2.2" fill="#111" stroke="none" />
        <path d="M14 23h14" />
      </g>
    ) : (
      <g fill="#111">
        <circle cx="15" cy="14" r="2.4" />
        <circle cx="27" cy="14" r="2.4" />
        <path d="M14 22.5c2.6 3.2 5 4.6 7 4.6s4.4-1.4 7-4.6c-3 1.2-11 1.2-14 0Z" />
      </g>
    );
  return (
    <svg
      width="44"
      height="44"
      viewBox="0 0 42 42"
      role="img"
      aria-label="Decorative character mark"
      className="mark"
    >
      <circle cx="21" cy="21" r="20" fill="#fff" stroke={color} strokeWidth="2" />
      {content}
    </svg>
  );
}

export function AvatarRow() {
  return (
    <div className="marksRow" aria-hidden="true">
      {MARK_COLORS.concat(MARK_COLORS.slice(0, 3)).map((color, index) => (
        <AvatarMark key={index} color={color} variant={index} />
      ))}
    </div>
  );
}

export function Squiggle({ style }: { style?: React.CSSProperties }) {
  return (
    <svg width="60" height="26" viewBox="0 0 60 26" fill="none" aria-hidden="true" style={style}>
      <path
        d="M2 18c6-14 12-14 18 0s12 14 18 0 12-14 18 0"
        stroke="#f64932"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function Sparkle({ style }: { style?: React.CSSProperties }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true" style={style}>
      <path
        d="M12 2c.7 5.4 3 8.6 8 8-5 .6-7.3 2.6-8 8-.7-5.4-3-7.4-8-8 5-.6 7.3-2.6 8-8Z"
        fill="#097fe8"
      />
    </svg>
  );
}

export function Flower({ style }: { style?: React.CSSProperties }) {
  const petal = (
    <>
      <circle cx="12" cy="5" r="4" fill="#ffb110" />
      <circle cx="19" cy="12" r="4" fill="#62aef0" />
      <circle cx="12" cy="19" r="4" fill="#f64932" />
      <circle cx="5" cy="12" r="4" fill="#b18164" />
      <circle cx="12" cy="12" r="2.6" fill="#fff" stroke="#111" strokeWidth="1.5" />
    </>
  );
  return (
    <svg width="30" height="30" viewBox="0 0 24 24" fill="none" aria-hidden="true" style={style}>
      {petal}
    </svg>
  );
}
