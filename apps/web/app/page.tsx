import Link from "next/link";
import { HeroRender } from "@/components/HeroRender";

const TICKER = [
  "Taste fit, not a visitor forecast",
  "Qloo decides",
  "Arrivals you own",
  "Grounded briefs",
  "Every number traceable",
  "Untapped markets first",
];

const STEPS = [
  {
    index: "01",
    kicker: "Profile",
    title: "Describe the destination",
    body:
      "Name it, add signature dishes, landmarks, music and more. TasteBound resolves each item to a real Qloo entity and shows what it could not resolve.",
  },
  {
    index: "02",
    kicker: "Score",
    title: "Measure taste lift",
    body:
      "Every origin market gets a taste score from Qloo affinity lift over a popularity baseline, with coverage, confidence and thin-data flags in the open.",
  },
  {
    index: "03",
    kicker: "Compare",
    title: "Find the gap",
    body:
      "Bring your arrivals CSV. The gap quadrant shows where taste is strong but arrivals are not — with audiences, angles, partners and a budget split.",
  },
];

const SOURCES = [
  "Qloo Taste Graph",
  "Your arrivals CSV",
  "Gemma 4 on Ollama Cloud",
  "Next.js + FastAPI",
];

export default function LandingPage() {
  return (
    <main className="page">
      <section className="hero" aria-labelledby="hero-title">
        <div className="heroCopy">
          <span className="eyebrow">Qloo Agentic Hackathon / 2026</span>
          <h1 id="hero-title" className="display">
            Find the markets that <span className="heroPill">already share</span> your taste.
          </h1>
          <p className="heroSub">
            TasteBound builds a Qloo taste profile for a destination, scores origin markets by taste
            lift over a popularity baseline, compares that with real arrivals — and shows you the
            untapped markets worth a campaign.
          </p>
          <div className="heroActions">
            <Link className="btnPrimary" href="/start">
              Start a run
            </Link>
            <Link className="btnGhost" href="/sample">
              See a sample run
            </Link>
          </div>
          <p className="heroMeta">
            <span>Taste fit, not a visitor forecast</span>
            <span>Stored sample, no sign-up</span>
          </p>
        </div>

        <div className="heroVisual">
          <HeroRender />
          <div className="heroCaption">
            <span>Physical signals / digital taste</span>
            <span>Qloo entity graph</span>
          </div>
        </div>
      </section>

      <div className="ticker" aria-hidden="true">
        <div className="tickerTrack">
          {[...TICKER, ...TICKER].map((item, index) => (
            <span key={`${item}-${index}`}>{item}</span>
          ))}
        </div>
      </div>

      <section id="how" className="section" aria-labelledby="how-title">
        <div className="sectionHeader">
          <div className="stackSm">
            <span className="eyebrow">Method / three moves</span>
            <h2 id="how-title" className="displaySm">
              From a destination to a decision.
            </h2>
          </div>
          <p className="muted">
            No black boxes, no visitor claims. Each step is deterministic code over Qloo responses,
            with the model limited to proposals and prose.
          </p>
        </div>

        <div className="grid3">
          {STEPS.map((step, index) => (
            <article
              key={step.index}
              className={`card stepCard${index === 1 ? " stepCardDark" : ""}`}
            >
              <div className="stepIndex">
                <span>Step {step.index}</span>
                <strong aria-hidden="true">{step.index}</strong>
              </div>
              <span className="kindTag">{step.kicker}</span>
              <h3 className="headingSm">{step.title}</h3>
              <p>{step.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section grid2" aria-labelledby="gap-title">
        <article className="cardDark stack">
          <span className="kindTag">The gap quadrant</span>
          <h2 id="gap-title" className="headingSm">
            Strong taste. Few arrivals.
          </h2>
          <p className="muted">
            Taste score on one axis, arrivals share on the other. Untapped markets sit top-left:
            strong taste fit, few visitors today. Every point opens the full market brief.
          </p>
          <div className="quadrantPreview" aria-hidden="true">
            <div className="quadrantZone">
              <span>Untapped</span>
              <i className="dot dotMint" style={{ left: "58%", top: "62%" }} />
              <i className="dot dotMint" style={{ left: "28%", top: "34%", width: 9, height: 9 }} />
            </div>
            <div className="quadrantZone">
              <span>Core</span>
              <i className="dot" style={{ left: "62%", top: "38%" }} />
              <i className="dot" style={{ left: "36%", top: "58%", width: 8, height: 8 }} />
            </div>
            <div className="quadrantZone">
              <span>Low priority</span>
              <i className="dot dotMuted" style={{ left: "48%", top: "44%" }} />
            </div>
            <div className="quadrantZone">
              <span>Habit</span>
              <i className="dot dotYellow" style={{ left: "56%", top: "58%" }} />
            </div>
          </div>
        </article>

        <article className="card stack">
          <span className="kindTag">Audit trail</span>
          <h2 className="headingSm">Every number has a source.</h2>
          <p className="muted">
            Each score, gap, audience and partner links back to the Qloo call that produced it. The
            trace page lists every call, tool step and warning in order.
          </p>
          <dl className="kv">
            <dt>Taste score</dt>
            <dd className="num">percentile of lift</dd>
            <dt>Lift</dt>
            <dd className="num">target − baseline</dd>
            <dt>Gap</dt>
            <dd className="num">taste − arrivals</dd>
          </dl>
          <div>
            <Link className="btnOutline" href="/sample">
              Open the sample run
            </Link>
          </div>
        </article>
      </section>

      <section className="darkBand onDark" aria-labelledby="principles-title">
        <div className="darkBandInner">
          <div className="sectionHeader">
            <div className="stackSm">
              <span className="eyebrow eyebrowOnDark">Principles / non-negotiable</span>
              <h2 id="principles-title" className="displaySm">
                Qloo decides. The model narrates.
              </h2>
            </div>
            <p className="muted">
              The agent proposes item names, chooses tools and writes briefs that must pass a
              grounding validator. Scores, gaps, audiences, angle evidence and partners stay in
              deterministic code.
            </p>
          </div>

          <div className="featureBand">
            <div className="featureItem">
              <span className="kindTag">01 / Signals</span>
              <h3 className="headingSm">Scores from Qloo</h3>
              <p>
                Affinity lift over a popularity baseline. Percentile-ranked within the run, never
                dressed up as a visitor forecast.
              </p>
            </div>
            <div className="featureItem">
              <span className="kindTag">02 / Language</span>
              <h3 className="headingSm">Briefs with receipts</h3>
              <p>
                Model-written prose is labelled and checked against evidence. Without a model, the
                template is labelled too.
              </p>
            </div>
            <div className="featureItem">
              <span className="kindTag">03 / Failure</span>
              <h3 className="headingSm">Fail closed</h3>
              <p>
                No Qloo key, no ranking. The kill switch is a tested feature, not an error path that
                quietly invents numbers.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="sources-title">
        <div className="sectionHeader">
          <div className="stackSm">
            <span className="eyebrow">Built with</span>
            <h2 id="sources-title" className="headingSm">
              Taste graph in. Campaign plan out.
            </h2>
          </div>
          <p className="muted">
            One portable stack: Qloo for taste, your data for arrivals, a grounded agent for the
            words.
          </p>
        </div>
        <div className="logoWall" aria-label="What TasteBound combines">
          {SOURCES.map((source) => (
            <span key={source} className="logoWallItem">
              {source}
            </span>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="ctaPanel">
          <span className="eyebrow">Start with one destination</span>
          <h2 className="displaySm">Find the markets already leaning in.</h2>
          <p>
            The sample is a stored, read-only run for a real destination — no Qloo quota, no
            sign-up. Or bring your own destination and arrivals.
          </p>
          <div className="heroActions">
            <Link className="btnPrimary" href="/start">
              Start a run
            </Link>
            <Link className="btnGhost" href="/sample">
              See a sample run
            </Link>
          </div>
          <p className="caption">Taste fit, not a visitor forecast. No visitor claims, no black boxes.</p>
        </div>
      </section>
    </main>
  );
}
