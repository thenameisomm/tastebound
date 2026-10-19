# 17. Judging

## Official rules (read Oct 19, 2026; re-check before submitting)

- **Theme:** "Agents, but with taste." Build an agentic tool, an agent-powered app, or wire Qloo into an existing agent. *"If your submission would work the same without Qloo, you're building the wrong thing."*
- **Must:** working software integrating the Qloo API that (a) functions as an agentic tool, (b) is built with an agent framework, or (c) integrates Qloo into an existing agent.
- **Submit (re-checked against https://qloo.devpost.com on Oct 19, 2026):** a functional demo application, **hosted externally and fully published** (local-only or private access does not qualify); a public repo (GitHub/GitLab/Bitbucket) with an open-source licence file **visible in the About section**; a text description. **Demo videos are NOT required.** Free, unrestricted testing for judges; judges can use the app directly.
- **Stage 1:** pass/fail viability. **Stage 2 (equal weight):** Technological Implementation ("How thoroughly and skillfully does the project use Qloo?"), Design ("complete, coherent product experience, not just a technical proof of concept"), Potential Impact ("credible, specific case for solving a real problem for a real audience"), Quality of the Idea ("creative, non-obvious use of Qloo and does the team demonstrate genuine understanding"). **Tie-break:** Technological Implementation first.
- **Prizes:** $15,000 / $6,000 / $4,000; Jason Calacanis invests $25,000 in his favourite entry. The judging panel is business- and investor-heavy.

## What Qloo wants vs what TasteBound provides

| Qloo wants | TasteBound provides | Proof in the demo |
|---|---|---|
| Thorough, skilful use of Qloo | 5+ capabilities in a dependent chain; baseline lift; guards; cache; budget; trace | Trace page; call counter; lift vs raw example |
| Impossible without Qloo | Kill switch; no other source can map cross-domain taste to origin markets | Invalid key on camera |
| Agentic | LLM proposes profile items and writes grounded briefs; deterministic orchestration is recorded | Run detail shows orchestration; trace of every tool and Qloo step |
| Complete product | Intake → profile → quadrant → deep dive → budget → briefs → export | One uninterrupted flow |
| Real problem, real audience | DMOs with shrinking budgets; median ~$1.77M; Brand USA cut (verify sources) | Cited statistic, real destination, real arrivals |
| Non-obvious use | Reverses travel recommenders: destination → origin markets; gap vs arrivals | Untapped quadrant |
| Genuine understanding | Baseline for popularity, brands-ignore-location handling, coverage limits stated | Limits panel, README |

## Self-score (independent judge agent and own review, Oct 19)

| Criterion | Base version | Gap-finder version, well executed | Main risk |
|---|---|---|---|
| Technological Implementation | 4 | 4–4.5 | Strategy fails outside the US |
| Design | 3.5 | 4 | Too much for 11 days; keep one polished case |
| Potential Impact | 3.5 | 4 | No proof taste predicts travel; backtest helps |
| Quality of the Idea | 3.5 | 4 | Seen as GeoTaste reversed; the gap angle answers it |
| **Total /20** | **14.5** | **~16** | |

Placement estimate: **plausible top 3 if executed very well**; around 13 if the gap view, validation and hosted demo are weak. No honest percentage exists (about 1,760 registrants).

## Hard questions and answers (use only if true after testing)

| Question | Answer |
|---|---|
| "DMOs already have Zartico, Datafy, ForwardKeys." | Those measure visits, spend and searches: people already coming. We measure latent taste fit and combine it with their arrivals data in the gap view. |
| "Does taste predict travel?" | Not on its own. We show it as a shortlist signal and report a backtest or blind review: [result]. |
| "Isn't this just big cities?" | Taste scores are lift over a popularity baseline; correlation with population band is [value]. |
| "Does Qloo cover non-US markets?" | We measured coverage per market; thin markets are flagged and get low confidence. |
| "Where's the agent?" | Gemma 4 on Ollama Cloud proposes the profile items and writes the briefs; tool orchestration is deterministic on purpose so Qloo decides, and every run records which path ran. The tool-choice loop is disabled until live tool calling is verified. |
| "Different from GeoTaste?" | GeoTaste analyses a location for a business. We start from a destination and find which origin markets to target, then add arrivals gaps, audiences, angles and partners. |

## Demo run-through (video not required; use as a script if recording anyway)

| Time | Beat |
|---|---|
| 0:00 | Problem: DMO budgets under pressure (cited figure); they only see people already coming |
| 0:15 | Enter the demo destination; signature items; profile resolves in Qloo |
| 0:40 | Select 30 markets + arrivals sample; run; Qloo call counter climbs |
| 1:05 | **Gap quadrant**: point out two untapped markets |
| 1:25 | Market detail: lift vs baseline, audience, angle with evidence, podcasts/artists/films/books |
| 1:55 | Budget slider; brief with evidence chips; export |
| 2:15 | Trace page for one number |
| 2:30 | Kill switch: invalid Qloo key → no plan |
| 2:45 | Evaluation result in one sentence; limits; who it's for |

## Devpost text skeleton

Name and tagline ("TasteBound: find the markets that already love your destination"); Inspiration (budgets, blind spot); What it does (5 bullets); How we built it (Turborepo, Next.js, FastAPI, Supabase, Gemma 4 on Ollama Cloud for item proposals and grounded briefs, deterministic tool orchestration, Qloo chain diagram); How Qloo is used (chain, baseline, gap, cross-domain partners, kill switch); Challenges (coverage, popularity bias, silent failures, cloud tool calling); Accomplishments (evaluation numbers, trace); What's next (more destinations, campaign tracking, DMO pilots); Built with.

## Run `docs/judge.md` before submitting

It spawns specialist reviewers that test every claim against the built app and produce `JUDGING_REPORT.md` with scores and a ranked fix list.
