import Link from "next/link";

export function Nav() {
  return (
    <nav className="nav">
      <Link href="/" className="brand">
        TasteBound<span className="brandDot">.</span>
      </Link>
      <div className="navLinks">
        <Link href="/sample" className="navLink">
          Sample run
        </Link>
        <Link href="/start" className="navLink">
          Start
        </Link>
      </div>
    </nav>
  );
}
