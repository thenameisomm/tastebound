export function HeroRender() {
  return (
    <svg
      className="heroArt"
      viewBox="0 0 600 600"
      role="img"
      aria-label="A sculptural concrete cube branded with taste signals, with mint, yellow and coral geometric pieces on top."
    >
      <defs>
        <clipPath id="cubeFaceClip">
          <polygon points="300,100 510,205 300,310 90,205" />
          <polygon points="90,205 300,310 300,500 90,395" />
          <polygon points="300,310 510,205 510,395 300,500" />
        </clipPath>
        <filter id="concreteGrain" x="-10%" y="-10%" width="120%" height="120%">
          <feTurbulence type="fractalNoise" baseFrequency="0.82" numOctaves="3" seed="7" result="noise" />
          <feColorMatrix in="noise" type="saturate" values="0" result="gray" />
          <feComponentTransfer in="gray">
            <feFuncA type="table" tableValues="0 0.16" />
          </feComponentTransfer>
        </filter>
        <pattern id="woodGrain" width="14" height="14" patternUnits="userSpaceOnUse">
          <rect width="14" height="14" fill="#c7b39c" />
          <path d="M0 3h14M0 9h14" stroke="#a08a71" strokeWidth="0.7" opacity="0.65" />
          <path d="M4 0v14" stroke="#b29b81" strokeWidth="0.5" opacity="0.45" />
        </pattern>
      </defs>

      {/* contact plane */}
      <ellipse cx="300" cy="515" rx="238" ry="30" fill="#d2d2d2" />
      <ellipse cx="300" cy="515" rx="160" ry="18" fill="#c4c4c4" />

      {/* main cube */}
      <polygon points="300,100 510,205 300,310 90,205" fill="#fafafa" stroke="#111111" strokeWidth="1.6" />
      <polygon points="90,205 300,310 300,500 90,395" fill="#d7d7d7" stroke="#111111" strokeWidth="1.6" />
      <polygon points="300,310 510,205 510,395 300,500" fill="#bdbdbd" stroke="#111111" strokeWidth="1.6" />

      {/* concrete grain */}
      <g clipPath="url(#cubeFaceClip)">
        <rect x="80" y="90" width="440" height="420" filter="url(#concreteGrain)" opacity="0.62" />
      </g>

      {/* wood inlay on the left face */}
      <polygon points="120,236 270,311 270,450 120,375" fill="url(#woodGrain)" stroke="#111111" strokeWidth="1.4" />

      {/* brand plates */}
      <g transform="translate(142 292) skewY(26.565) scale(1 0.9)">
        <text
          fontFamily="var(--font-mono)"
          fontSize="11"
          letterSpacing="1.6"
          fill="#111111"
          opacity="0.85"
        >
          QLOO
        </text>
        <text
          y="17"
          fontFamily="var(--font-mono)"
          fontSize="8"
          letterSpacing="1.2"
          fill="#111111"
          opacity="0.55"
        >
          TASTE SIGNAL / 01
        </text>
      </g>

      <polygon points="332,349 470,280 470,331 332,400" fill="#ffffff" stroke="#111111" strokeWidth="1.4" />
      <g transform="translate(345 360) skewY(-26.565) scale(1 0.9)">
        <text fontFamily="var(--font-mono)" fontSize="11" letterSpacing="1.6" fill="#111111">
          TASTE FIT
        </text>
        <text
          y="17"
          fontFamily="var(--font-mono)"
          fontSize="8"
          letterSpacing="1.2"
          fill="#111111"
          opacity="0.55"
        >
          NOT A FORECAST
        </text>
      </g>

      <g transform="translate(267 187)">
        <text fontFamily="var(--font-mono)" fontSize="9" letterSpacing="1.8" fill="#111111" opacity="0.72">
          TB / 26
        </text>
      </g>

      {/* mint cylinder */}
      <path d="M382 163v56a38 16 0 0 0 76 0v-56Z" fill="#d1ffca" stroke="#111111" strokeWidth="1.5" />
      <ellipse cx="420" cy="163" rx="38" ry="16" fill="#e8ffe5" stroke="#111111" strokeWidth="1.5" />
      <ellipse cx="420" cy="219" rx="38" ry="16" fill="#d1ffca" opacity="0.45" />

      {/* yellow sphere resting on the top edge */}
      <circle cx="164" cy="228" r="35" fill="#fff100" stroke="#111111" strokeWidth="1.6" />
      <path d="M142 246a35 35 0 0 0 45 0" fill="none" stroke="#111111" strokeWidth="1.2" opacity="0.45" />

      {/* coral wedge */}
      <polygon points="248,142 288,162 248,182 208,162" fill="#ff8f7b" stroke="#111111" strokeWidth="1.5" />
      <polygon points="208,162 248,182 248,214 208,194" fill="#ef7e6b" stroke="#111111" strokeWidth="1.5" />
      <polygon points="248,182 288,162 288,194 248,214" fill="#dc6c5b" stroke="#111111" strokeWidth="1.5" />

      {/* black peg */}
      <rect x="317" y="128" width="12" height="42" rx="6" fill="#111111" />
      <circle cx="323" cy="126" r="12" fill="#111111" />

      {/* floating tags */}
      <g transform="translate(52 116)">
        <rect width="136" height="36" rx="18" fill="#d1ffca" />
        <text x="18" y="23" fontFamily="var(--font-mono)" fontSize="9" letterSpacing="1.4" fill="#111111">
          UNTAPPED / 01
        </text>
      </g>
      <g transform="translate(430 80)">
        <rect width="126" height="36" rx="18" fill="#fff100" />
        <text x="18" y="23" fontFamily="var(--font-mono)" fontSize="9" letterSpacing="1.4" fill="#111111">
          ARRIVALS
        </text>
      </g>

      {/* editorial registration marks */}
      <path d="M58 566h44M80 544v44" stroke="#111111" strokeWidth="1" opacity="0.35" />
      <path d="M498 566h44M520 544v44" stroke="#111111" strokeWidth="1" opacity="0.35" />
      <path d="M58 72V28h44" fill="none" stroke="#111111" strokeWidth="1" opacity="0.25" />
      <path d="M542 72V28h-44" fill="none" stroke="#111111" strokeWidth="1" opacity="0.25" />
    </svg>
  );
}
