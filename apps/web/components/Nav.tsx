import Link from "next/link";

export function Nav() {
  return (
    <nav className="nav" aria-label="Main">
      <Link href="/" className="brand">
        TasteBound<span className="brandDot">.</span>
      </Link>
      <div className="navLinks">
        <Link href="/#how" className="navLink">
          How it works
        </Link>
        <Link href="/sample" className="navLink">
          Sample run
        </Link>
      </div>
      <div className="navActions">
        <Link href="/start" className="btnPrimary">
          Start a run
        </Link>
      </div>
    </nav>
  );
}
