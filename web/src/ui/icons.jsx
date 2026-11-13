// Small authored icon set: 20px grid, 1.75 stroke, round joins.
const Svg = ({ children, ...props }) => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 20 20"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    {...props}
  >
    {children}
  </svg>
)

export const PlayIcon = () => (
  <Svg>
    <path d="M6.5 4.5v11l9-5.5z" fill="currentColor" stroke="none" />
  </Svg>
)

export const PauseIcon = () => (
  <Svg>
    <path d="M7 4.5v11M13 4.5v11" strokeWidth="2.25" />
  </Svg>
)

export const ResetIcon = () => (
  <Svg>
    <path d="M4.5 10a5.5 5.5 0 1 0 1.7-4" />
    <path d="M4.5 3.5V7H8" />
  </Svg>
)

export const SlidersIcon = () => (
  <Svg>
    <path d="M4 6h7M15 6h1M4 14h1M9 14h7" />
    <circle cx="13" cy="6" r="2" />
    <circle cx="7" cy="14" r="2" />
  </Svg>
)

export const CloseIcon = () => (
  <Svg>
    <path d="M5 5l10 10M15 5L5 15" />
  </Svg>
)

export const TapIcon = () => (
  <Svg>
    <path d="M8 9V4.5a1.5 1.5 0 0 1 3 0V9" />
    <path d="M11 8.5a1.5 1.5 0 0 1 3 0v3.5a4.5 4.5 0 0 1-4.5 4.5H9a4 4 0 0 1-3.3-1.8L4 12.2a1.4 1.4 0 0 1 2.2-1.7L8 12" />
  </Svg>
)
