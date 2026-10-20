import Link from "next/link";

export function Footer() {
  return (
    <footer className="footer">
      <div className="footerInner">
        <div className="footerTop">
          <div>
            <p className="footerBrand">
              TasteBound<span>.</span>
            </p>
            <p className="footerTagline">
              Taste fit, not a visitor forecast. Qloo decides, the model narrates, and every number
              traces back to the call that produced it.
            </p>
          </div>
          <nav className="footerLinks" aria-label="Footer">
            <Link href="/#how">How it works</Link>
            <Link href="/analytics">Analytics</Link>
            <Link href="/sample">Sample run</Link>
            <Link href="/start">Start a run</Link>
          </nav>
        </div>
        <div className="footerBottom">
          <span>Built for the Qloo Agentic Hackathon 2026</span>
          <span>Qloo signals · your arrivals · grounded briefs</span>
          <span>© 2026 TasteBound</span>
        </div>
      </div>
    </footer>
  );
}
