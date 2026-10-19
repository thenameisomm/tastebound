import Link from "next/link";
import { AvatarRow, Sparkle, Squiggle } from "@/components/Marks";

const MOCK_MARKETS = [
  { city: "New York", score: 98.7, width: "95%", fill: "#097fe8", label: "untapped", pill: "pillGood" },
  { city: "Los Angeles", score: 97.2, width: "90%", fill: "#62aef0", label: "untapped", pill: "pillGood" },
  { city: "Chicago", score: 95.8, width: "86%", fill: "#ffb110", label: "growing", pill: "pillWarn" },
  { city: "San Diego", score: 94.9, width: "82%", fill: "#b18164", label: "core", pill: "pill" },
  { city: "Seattle", score: 93.4, width: "79%", fill: "#097fe8", label: "core", pill: "pill" },
];

export default function LandingPage() {
  return (
    <main className="page">
      <section className="hero">
        <div className="heroDecor" style={{ left: "4%", top: 96 }}>
          <Squiggle />
        </div>
        <div className="heroDecor" style={{ right: "6%", top: 150 }}>
          <Sparkle />
        </div>
        <AvatarRow />
        <div className="heroCopy">
          <span className="pill pillWarm">Qloo Agentic Hackathon 2026</span>
          <h1 className="display">
            Find the markets that <span className="heroPill">already share</span> your taste.
          </h1>
          <p className="heroSub">
            TasteBound builds a taste profile for your US destination with Qloo, scores domestic
            origin markets by taste lift over a popularity baseline, compares that with real
            domestic arrivals — and shows you the untapped US markets worth a campaign.
          </p>
          <div className="row" style={{ justifyContent: "center", gap: 12 }}>
            <Link className="btnPrimary" href="/start" style={{ padding: "12px 24px", fontSize: 16 }}>
              Start a run
            </Link>
            <Link className="btnGhost" href="/sample" style={{ padding: "12px 24px", fontSize: 16 }}>
              See a sample run
            </Link>
          </div>
          <p className="caption" style={{ maxWidth: 560 }}>
            Taste fit, not a visitor forecast. Scores come from Qloo signals; arrivals come from the
            CSV you upload. No demand claims, no black boxes.
          </p>
        </div>
        <div className="mockup" aria-hidden="true">
          <div className="mockupBar">
            <span className="mockupDot" />
            <span className="mockupDot" />
            <span className="mockupDot" />
          </div>
          <div className="mockupBody">
            {MOCK_MARKETS.map((market) => (
              <div className="mockupRow" key={market.city}>
                <span>{market.city}</span>
                <span className="mockupTrack">
                  <span className="mockupFill" style={{ width: market.width, background: market.fill }} />
                </span>
                <span className={`pill ${market.pill}`}>
                  {market.label} · {market.score.toFixed(1)}
                </span>
              </div>
            ))}
          </div>
          <div className="mockupFoot">
            <span className="pill pillSky">taste fit percentile</span>
            <span className="caption">from Qloo lift over a popularity baseline</span>
          </div>
        </div>
      </section>

      <section id="how" className="section grid3">
        <div className="card stack">
          <span className="pill pillSky">1 · Profile</span>
          <h2 className="headingSm">Describe the destination</h2>
          <p className="muted">
            Name it, add signature dishes, landmarks, music and more — TasteBound resolves each one
            to a real Qloo entity and shows what it could not resolve.
          </p>
        </div>
        <div className="card stack">
          <span className="pill pillWarm">2 · Score</span>
          <h2 className="headingSm">Score origin markets</h2>
          <p className="muted">
            Every market gets a taste score from Qloo affinity lift over a popularity baseline, with
            coverage, confidence and thin-data flags in the open.
          </p>
        </div>
        <div className="card stack">
          <span className="pill pillGood">3 · Compare</span>
          <h2 className="headingSm">Find the gap</h2>
          <p className="muted">
            Upload arrival numbers. The gap quadrant shows where taste is strong but arrivals are
            not — with audiences, angles, partners and a budget split you can export.
          </p>
        </div>
      </section>

      <section className="section grid2">
        <div className="cardAccent stack">
          <h2 className="headingSm">The domestic gap quadrant</h2>
          <p>
            Taste score on one axis, domestic arrivals share on the other. Untapped US markets
            sit top-left: strong taste fit, few domestic visitors today.
          </p>
        </div>
        <div className="cardDark stack">
          <h2 className="headingSm">Everything traceable</h2>
          <p>
            Each number links back to the Qloo call that produced it. The trace page lists every
            call, tool step and warning — audit the whole run.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="logoWall" aria-label="What TasteBound combines">
          <span className="logoWallItem">Qloo Taste Graph</span>
          <span className="logoWallItem">Your arrivals CSV</span>
          <span className="logoWallItem">Gemma 4 on Ollama Cloud</span>
          <span className="logoWallItem">Next.js + FastAPI</span>
        </div>
      </section>

      <section className="section">
        <div className="card stack" style={{ alignItems: "center", textAlign: "center", padding: "48px 24px" }}>
          <p className="subheading">Try it for your US destination</p>
          <p className="muted" style={{ maxWidth: 480 }}>
            The sample run is a stored, read-only run — no Qloo quota, no sign-up.
            Explore domestic taste fit for a US city.
          </p>
          <Link className="btnPrimary" href="/sample">
            Open the US sample run
          </Link>
        </div>
      </section>
    </main>
  );
}
