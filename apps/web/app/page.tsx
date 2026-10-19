import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="page">
      <section className="stack" style={{ maxWidth: 840, paddingTop: 64 }}>
        <span className="pill pillWarm" style={{ alignSelf: "flex-start" }}>
          Qloo Agentic Hackathon 2026
        </span>
        <h1 className="display">
          Find the markets that <span className="heroPill">already share</span> your taste.
        </h1>
        <p className="serif" style={{ fontSize: 20, maxWidth: 640 }}>
          TasteBound builds a taste profile for your destination with Qloo, scores origin markets by
          taste lift over a popularity baseline, compares that with real arrivals — and shows you the
          untapped markets worth a campaign.
        </p>
        <div className="row" style={{ gap: 12 }}>
          <Link className="btnPrimary" href="/start" style={{ padding: "12px 24px", fontSize: 16 }}>
            Start a run
          </Link>
          <Link className="btnGhost" href="/sample" style={{ padding: "12px 24px", fontSize: 16 }}>
            See a sample run
          </Link>
        </div>
        <p className="caption">
          Taste fit, not a visitor forecast. Scores come from Qloo signals; arrivals come from the CSV
          you upload. No demand claims, no black boxes.
        </p>
      </section>

      <section className="section grid3">
        <div className="card stack">
          <span className="pill pillSky">1 · Profile</span>
          <h2 className="headingSm">Describe the destination</h2>
          <p className="muted">
            Name it, add signature dishes, landmarks, music and more — TasteBound resolves each one to
            a real Qloo entity and shows what it could not resolve.
          </p>
        </div>
        <div className="card stack">
          <span className="pill pillSky">2 · Score</span>
          <h2 className="headingSm">Score origin markets</h2>
          <p className="muted">
            Every market gets a taste score from Qloo affinity lift over a popularity baseline, with
            coverage, confidence and thin-data flags in the open.
          </p>
        </div>
        <div className="card stack">
          <span className="pill pillSky">3 · Compare</span>
          <h2 className="headingSm">Find the gap</h2>
          <p className="muted">
            Upload arrival numbers. The gap quadrant shows where taste is strong but arrivals are not
            — with audiences, angles, partners and a budget split you can export.
          </p>
        </div>
      </section>

      <section className="section grid2">
        <div className="cardAccent stack">
          <h2 className="headingSm">The gap quadrant</h2>
          <p>
            Taste score on one axis, arrivals share on the other. Untapped markets sit top-left:
            strong taste fit, few visitors today.
          </p>
        </div>
        <div className="cardDark stack">
          <h2 className="headingSm">Everything traceable</h2>
          <p>
            Each number links back to the Qloo call that produced it. The trace page lists every call,
            tool step and warning — audit the whole run.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="empty">
          <p className="subheading">Try it without keys</p>
          <p className="muted" style={{ marginTop: 8 }}>
            The sample run is a stored, read-only run — no Qloo quota, no sign-up.
          </p>
          <Link className="btnPrimary" href="/sample" style={{ marginTop: 16 }}>
            Open the sample run
          </Link>
        </div>
      </section>
    </main>
  );
}
