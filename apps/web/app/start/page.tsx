"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Banner } from "@/components/Banner";
import { ErrorPanel } from "@/components/ErrorPanel";
import { EmptyState } from "@/components/EmptyState";
import { SourceChip } from "@/components/SourceChip";
import type {
  ArrivalsResponse,
  ArrivalsSampleOut,
  DestinationResponse,
  IntakeResponse,
  ItemKind,
  MarketOut,
  PresetOut,
  ProfilePreviewResponse,
  SignatureItemInput,
} from "@/lib/types";

const KINDS: { id: ItemKind; label: string }[] = [
  { id: "landmark", label: "Landmark" },
  { id: "neighbourhood", label: "Neighbourhood" },
  { id: "dish", label: "Dish" },
  { id: "drink", label: "Drink" },
  { id: "venue", label: "Venue" },
  { id: "festival", label: "Festival" },
  { id: "music", label: "Music" },
  { id: "film", label: "Film" },
  { id: "book", label: "Book" },
  { id: "brand", label: "Brand" },
];

const ORIGIN_LABELS: Record<string, string> = {
  llm_website: "from website",
  llm_name_only: "general knowledge",
  user: "yours",
};

const PRESET_LABELS: Record<string, string> = {
  europe20: "Europe (20)",
  na15: "North America (15)",
  apac15: "Asia-Pacific (15)",
  me8: "Middle East (8)",
  latam10: "Latin America (10)",
};

type Step = 1 | 2 | 3 | 4;

export default function StartPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);

  const [name, setName] = useState("");
  const [country, setCountry] = useState("");
  const [website, setWebsite] = useState("");

  const [items, setItems] = useState<SignatureItemInput[]>([]);
  const [intakeNotice, setIntakeNotice] = useState<string | null>(null);
  const [intakeSource, setIntakeSource] = useState<string | null>(null);

  const [destinationId, setDestinationId] = useState<string | null>(null);
  const [profile, setProfile] = useState<ProfilePreviewResponse | null>(null);
  const [profileStale, setProfileStale] = useState(false);

  const [markets, setMarkets] = useState<MarketOut[]>([]);
  const [presets, setPresets] = useState<PresetOut[]>([]);
  const [region, setRegion] = useState("all");
  const [marketQuery, setMarketQuery] = useState("");
  const [selected, setSelected] = useState<string[]>([]);

  const [samples, setSamples] = useState<ArrivalsSampleOut[]>([]);
  const [arrivals, setArrivals] = useState<ArrivalsResponse | null>(null);
  const [sourceNote, setSourceNote] = useState("");
  const [sampleId, setSampleId] = useState<string>("");
  const fileRef = useRef<HTMLInputElement | null>(null);

  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchType, setSearchType] = useState("place");
  const [searchResults, setSearchResults] = useState<{ entity_id: string; name: string; type: string }[]>([]);

  const run = async <T,>(label: string, fn: () => Promise<T>): Promise<T | undefined> => {
    setBusy(label);
    setError(null);
    try {
      return await fn();
    } catch (err) {
      setError(err);
      return undefined;
    } finally {
      setBusy(null);
    }
  };

  useEffect(() => {
    if (step !== 4 || markets.length > 0) return;
    void run("markets", async () => {
      const payload = await api.get<{ markets: MarketOut[]; presets: PresetOut[] }>("/v1/markets");
      setMarkets(payload.markets);
      setPresets(payload.presets);
    });
    void run("samples", async () => {
      const payload = await api.get<ArrivalsSampleOut[]>("/v1/arrivals/samples");
      setSamples(payload);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  const suggest = async () => {
    const payload = await run("suggest", () =>
      api.post<IntakeResponse>("/v1/destinations/intake", {
        name,
        country_code: country,
        website_url: website || null,
      }),
    );
    if (!payload) return;
    const merged = [...items];
    const seen = new Set(merged.map((item) => item.name.toLowerCase()));
    for (const item of payload.items) {
      if (seen.has(item.name.toLowerCase())) continue;
      seen.add(item.name.toLowerCase());
      merged.push({ name: item.name, kind: item.kind, origin: item.origin });
    }
    setItems(merged.slice(0, 15));
    setIntakeNotice(payload.notice ?? null);
    setIntakeSource(payload.source);
    setStep(2);
  };

  const createDestination = async () => {
    const payload = await run("create", () =>
      api.post<DestinationResponse>("/v1/destinations", {
        name,
        country_code: country,
        website_url: website || null,
        items,
      }),
    );
    if (!payload) return;
    setDestinationId(payload.destination_id);
    setProfileStale(true);
    setStep(3);
    await resolveProfile(payload.destination_id, items);
  };

  const resolveProfile = async (destId = destinationId, itemList = items) => {
    if (!destId) return;
    const payload = await run("profile", async () => {
      await api.patch<DestinationResponse>(`/v1/destinations/${destId}`, { items: itemList });
      return api.post<ProfilePreviewResponse>(`/v1/destinations/${destId}/profile-preview`);
    });
    if (!payload) return;
    setProfile(payload);
    setProfileStale(false);
  };

  const searchQloo = async () => {
    const payload = await run("search", () =>
      api.get<{ entities: { entity_id: string; name: string; type: string }[] }>(
        `/v1/qloo/search?q=${encodeURIComponent(searchQuery)}&type=${searchType}`,
      ),
    );
    if (!payload) return;
    setSearchResults(payload.entities);
  };

  const addFromSearch = (entity: { entity_id: string; name: string; type: string }) => {
    const kind: ItemKind =
      entity.type === "artist" ? "music" : entity.type === "brand" ? "brand" : "landmark";
    if (items.some((item) => item.name.toLowerCase() === entity.name.toLowerCase())) return;
    setItems([...items, { name: entity.name, kind, origin: "user" }]);
    setProfileStale(true);
  };

  const uploadArrivals = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file && !sampleId) {
      setError(new Error("Attach a CSV file or pick a bundled sample."));
      return;
    }
    const form = new FormData();
    form.set("source_note", sourceNote || "Uploaded in the wizard");
    if (file) {
      form.set("file", file);
    } else {
      form.set("sample_id", sampleId);
    }
    const payload = await run("arrivals", () =>
      api.postForm<ArrivalsResponse>("/v1/arrivals", form),
    );
    if (payload) setArrivals(payload);
  };

  const startRun = async () => {
    const payload = await run("start", () =>
      api.post<{ run_id: string }>("/v1/runs", {
        destination_id: destinationId,
        market_ids: selected,
        arrivals_dataset_id: arrivals?.dataset_id ?? null,
      }),
    );
    if (payload) router.push(`/runs/${payload.run_id}`);
  };

  const filteredMarkets = useMemo(
    () =>
      markets.filter((market) => {
        if (region !== "all" && market.region !== region) return false;
        if (marketQuery && !`${market.city} ${market.country_name}`.toLowerCase().includes(marketQuery.toLowerCase()))
          return false;
        return true;
      }),
    [markets, region, marketQuery],
  );

  const regions = useMemo(() => Array.from(new Set(markets.map((market) => market.region))).sort(), [markets]);

  const toggleMarket = (marketId: string) => {
    setSelected((current) =>
      current.includes(marketId) ? current.filter((id) => id !== marketId) : [...current, marketId],
    );
  };

  return (
    <main className="page pageNarrow">
      <div className="stack" style={{ marginTop: 32 }}>
        <h1 className="heading">Start a run</h1>
        <div className="steps" role="list" aria-label="Wizard steps">
          {(
            [
              [1, "Destination"],
              [2, "Signature items"],
              [3, "Taste profile"],
              [4, "Markets & arrivals"],
            ] as [Step, string][]
          ).map(([index, label]) => (
            <div
              key={index}
              role="listitem"
              className={`step ${step === index ? "stepActive" : ""} ${step > index ? "stepDone" : ""}`}
            >
              <span className="stepNum">{index}</span>
              {label}
            </div>
          ))}
        </div>
      </div>

      {error ? <div className="sectionSm"><ErrorPanel error={error} /></div> : null}

      {step === 1 ? (
        <section className="card stack sectionSm">
          <h2 className="headingSm">Where is the destination?</h2>
          <div className="grid2">
            <label className="field">
              <span className="label">Destination name</span>
              <input
                className="input"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Lisbon"
                maxLength={120}
              />
            </label>
            <label className="field">
              <span className="label">Country code (ISO-2)</span>
              <input
                className="input"
                value={country}
                onChange={(event) => setCountry(event.target.value.toUpperCase().slice(0, 2))}
                placeholder="PT"
                maxLength={2}
              />
            </label>
          </div>
          <label className="field">
            <span className="label">Official website (optional)</span>
            <input
              className="input"
              type="url"
              value={website}
              onChange={(event) => setWebsite(event.target.value)}
              placeholder="https://www.visitlisboa.com"
            />
            <span className="caption">
              If provided, TasteBound reads up to 3 pages to suggest signature items.
            </span>
          </label>
          <div className="row">
            <button
              type="button"
              className="btnPrimary"
              disabled={busy !== null || name.trim().length < 2 || country.length !== 2}
              onClick={() => void suggest()}
            >
              {busy === "suggest" ? "Suggesting…" : "Suggest signature items"}
            </button>
            <button
              type="button"
              className="btnText"
              disabled={name.trim().length < 2 || country.length !== 2}
              onClick={() => setStep(2)}
            >
              I&apos;ll add items myself
            </button>
          </div>
        </section>
      ) : null}

      {step === 2 ? (
        <section className="card stack sectionSm">
          <div className="spread">
            <h2 className="headingSm">Signature items</h2>
            <span className="caption">{items.length}/15</span>
          </div>
          {intakeNotice ? <Banner tone="warn">{intakeNotice}</Banner> : null}
          {intakeSource ? (
            <span className="sourceChip" title="Where the suggestions came from">
              suggestions: {intakeSource === "website" ? "read from the website" : intakeSource === "general_knowledge" ? "model general knowledge" : "manual"}
            </span>
          ) : null}

          {KINDS.map((kind) => {
            const kindItems = items
              .map((item, index) => ({ item, index }))
              .filter(({ item }) => item.kind === kind.id);
            if (kindItems.length === 0) return null;
            return (
              <div key={kind.id} className="stackSm">
                <span className="kindTag">{kind.label}</span>
                <div className="row" style={{ gap: 8 }}>
                  {kindItems.map(({ item, index }) => (
                    <span key={`${item.name}-${index}`} className="chip">
                      {item.name}
                      <span className="caption" title="Where this item came from">
                        {ORIGIN_LABELS[item.origin] ?? item.origin}
                      </span>
                      <button
                        type="button"
                        aria-label={`Remove ${item.name}`}
                        onClick={() => setItems(items.filter((_, i) => i !== index))}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            );
          })}

          {items.length === 0 ? (
            <EmptyState title="No items yet">Add at least a few — they shape the whole taste profile.</EmptyState>
          ) : null}

          <AddItemRow
            onAdd={(item) => setItems([...items, item].slice(0, 15))}
            disabled={items.length >= 15}
          />

          <div className="row">
            <button type="button" className="btnText" onClick={() => setStep(1)}>
              Back
            </button>
            <button
              type="button"
              className="btnPrimary"
              disabled={busy !== null || items.length === 0}
              onClick={() => void createDestination()}
            >
              {busy === "create" ? "Creating…" : "Create destination"}
            </button>
          </div>
        </section>
      ) : null}

      {step === 3 ? (
        <section className="card stack sectionSm">
          <h2 className="headingSm">Taste profile</h2>
          {profile === null ? (
            <div className="stackSm">
              <div className="skeleton skeletonLine" style={{ width: "60%" }} />
              <div className="skeleton skeletonLine" style={{ width: "80%" }} />
              <div className="skeleton skeletonLine" style={{ width: "40%" }} />
            </div>
          ) : (
            <>
              {profile.warnings.map((warning) => (
                <Banner key={warning} tone="warn">
                  {warning}
                </Banner>
              ))}
              {profileStale ? (
                <Banner tone="info">
                  Items changed since this preview.{" "}
                  <button type="button" className="link" onClick={() => void resolveProfile()}>
                    Re-resolve
                  </button>
                </Banner>
              ) : null}

              <div className="stackSm">
                <span className="kindTag">Resolved entities</span>
                <ul className="stackSm" style={{ listStyle: "none" }}>
                  {profile.items.map((item) => (
                    <li key={`${item.name}-${item.role}`} className="row" style={{ gap: 8 }}>
                      <span
                        className={item.status === "resolved" ? "pill pillGood" : "pill pillWarn"}
                        title={item.note ?? (item.status === "resolved" ? "Matched to a Qloo entity" : "No Qloo match")}
                      >
                        {item.status}
                      </span>
                      <span style={{ fontWeight: item.role === "destination" ? 600 : 400 }}>
                        {item.entity_name ?? item.name}
                      </span>
                      <span className="caption">
                        {item.role === "destination" ? "destination" : item.kind}
                        {item.entity_type ? ` · ${item.entity_type}` : ""}
                        {item.similarity < 1 ? ` · similarity ${(item.similarity * 100).toFixed(0)}%` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              {profile.unresolved.length > 0 ? (
                <div className="stackSm">
                  <span className="kindTag">Unresolved</span>
                  <div className="row" style={{ gap: 6 }}>
                    {profile.unresolved.map((item) => (
                      <span key={item} className="pill pillWarn" title="No Qloo entity found — excluded from the profile">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {profile.tags.length > 0 ? (
                <div className="stackSm">
                  <span className="kindTag">Tags</span>
                  <div className="row" style={{ gap: 6 }}>
                    {profile.tags.slice(0, 20).map((tag, index) => {
                      const label = String((tag as { label?: string }).label ?? (tag as { name?: string }).name ?? "tag");
                      return (
                        <span key={`${label}-${index}`} className="pill">
                          {label}
                        </span>
                      );
                    })}
                  </div>
                </div>
              ) : null}

              <div className="stackSm">
                <span className="kindTag">Add from Qloo</span>
                <div className="row">
                  <input
                    className="input"
                    style={{ flex: 1, minWidth: 160 }}
                    placeholder="Search Qloo entities"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                  />
                  <select className="select" style={{ width: 140 }} value={searchType} onChange={(event) => setSearchType(event.target.value)}>
                    {["place", "destination", "locality", "artist", "brand", "tag"].map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="btnGhost"
                    disabled={busy !== null || searchQuery.trim().length < 2}
                    onClick={() => void searchQloo()}
                  >
                    {busy === "search" ? "Searching…" : "Search"}
                  </button>
                </div>
                {searchResults.length > 0 ? (
                  <ul className="stackSm" style={{ listStyle: "none" }}>
                    {searchResults.map((entity) => (
                      <li key={entity.entity_id} className="spread">
                        <span>
                          {entity.name} <span className="caption">{entity.type}</span>
                        </span>
                        <button type="button" className="btnOutline btnSmall" onClick={() => addFromSearch(entity)}>
                          Add
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </>
          )}

          <div className="row">
            <button type="button" className="btnText" onClick={() => setStep(2)}>
              Back
            </button>
            <button
              type="button"
              className="btnPrimary"
              disabled={busy !== null || !profile?.can_run}
              title={profile?.can_run ? undefined : "At least 3 items must resolve to Qloo entities"}
              onClick={() => setStep(4)}
            >
              Choose markets
            </button>
          </div>
        </section>
      ) : null}

      {step === 4 ? (
        <section className="card stack sectionSm">
          <div className="spread">
            <h2 className="headingSm">Markets</h2>
            <span className="pill" title="Pick 20–40 markets for a meaningful comparison">
              {selected.length} selected
            </span>
          </div>

          <div className="row">
            {presets.map((preset) => (
              <button
                key={preset.id}
                type="button"
                className="btnGhost btnSmall"
                onClick={() => setSelected(Array.from(new Set([...selected, ...preset.market_ids])))}
              >
                + {PRESET_LABELS[preset.id] ?? preset.label}
              </button>
            ))}
            <button type="button" className="btnText btnSmall" onClick={() => setSelected([])}>
              Clear
            </button>
          </div>

          <div className="row">
            <label className="field" style={{ minWidth: 170 }}>
              <span className="caption">Region</span>
              <select className="select" value={region} onChange={(event) => setRegion(event.target.value)}>
                <option value="all">All regions</option>
                {regions.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="field" style={{ flex: 1, minWidth: 180 }}>
              <span className="caption">Search</span>
              <input
                className="input"
                type="search"
                placeholder="City or country"
                value={marketQuery}
                onChange={(event) => setMarketQuery(event.target.value)}
              />
            </label>
          </div>

          <div
            className="stackSm"
            style={{ maxHeight: 320, overflowY: "auto", border: "1px solid rgba(0,0,0,0.08)", borderRadius: 12, padding: 12 }}
          >
            {filteredMarkets.map((market) => (
              <label key={market.id} className="checkRow">
                <input
                  type="checkbox"
                  checked={selected.includes(market.id)}
                  onChange={() => toggleMarket(market.id)}
                />
                <span>
                  {market.city}
                  <span className="caption"> · {market.country_name} · {market.region}</span>
                </span>
              </label>
            ))}
            {filteredMarkets.length === 0 ? <span className="muted">No markets match.</span> : null}
          </div>

          <div className="stackSm">
            <span className="kindTag">Arrivals (optional but unlocks the gap view)</span>
            <div className="row">
              <input ref={fileRef} className="input" type="file" accept=".csv,text/csv" style={{ maxWidth: 280 }} />
              <span className="caption">or</span>
              <select
                className="select"
                style={{ maxWidth: 260 }}
                value={sampleId}
                onChange={(event) => {
                  setSampleId(event.target.value);
                  if (fileRef.current) fileRef.current.value = "";
                }}
              >
                <option value="">Pick a bundled sample…</option>
                {samples.map((sample) => (
                  <option key={sample.id} value={sample.id}>
                    {sample.name}
                  </option>
                ))}
              </select>
            </div>
            <input
              className="input"
              placeholder="Source note (required) — e.g. Official tourism board 2024"
              value={sourceNote}
              onChange={(event) => setSourceNote(event.target.value)}
              maxLength={500}
            />
            <div className="row">
              <button type="button" className="btnGhost" disabled={busy !== null} onClick={() => void uploadArrivals()}>
                {busy === "arrivals" ? "Uploading…" : "Upload arrivals"}
              </button>
              {arrivals ? (
                <span className="row" style={{ gap: 6 }}>
                  <span className="pill pillGood" title="Arrivals parsed and matched to markets">
                    {arrivals.rows} rows · {arrivals.matched_markets} markets matched
                  </span>
                  {arrivals.is_sample ? <SourceChip label="bundled sample" title="This is a sample dataset bundled with TasteBound" /> : null}
                  {arrivals.notes.map((note) => (
                    <span key={note} className="caption">
                      {note}
                    </span>
                  ))}
                </span>
              ) : null}
            </div>
          </div>

          <div className="row">
            <button type="button" className="btnText" onClick={() => setStep(3)}>
              Back
            </button>
            <button
              type="button"
              className="btnPrimary"
              disabled={busy !== null || selected.length < 3 || !destinationId}
              onClick={() => void startRun()}
            >
              {busy === "start" ? "Starting…" : "Start the run"}
            </button>
            {selected.length > 0 && selected.length < 20 ? (
              <span className="caption">20–40 markets gives the most meaningful comparison.</span>
            ) : null}
          </div>
        </section>
      ) : null}
    </main>
  );
}

function AddItemRow({
  onAdd,
  disabled,
}: {
  onAdd: (item: SignatureItemInput) => void;
  disabled: boolean;
}) {
  const [value, setValue] = useState("");
  const [kind, setKind] = useState<ItemKind>("landmark");
  return (
    <div className="row">
      <input
        className="input"
        style={{ flex: 1, minWidth: 160 }}
        placeholder="Add your own item"
        value={value}
        maxLength={160}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && value.trim()) {
            onAdd({ name: value.trim(), kind, origin: "user" });
            setValue("");
          }
        }}
      />
      <select className="select" style={{ width: 150 }} value={kind} onChange={(event) => setKind(event.target.value as ItemKind)}>
        {KINDS.map((item) => (
          <option key={item.id} value={item.id}>
            {item.label}
          </option>
        ))}
      </select>
      <button
        type="button"
        className="btnGhost"
        disabled={disabled || !value.trim()}
        onClick={() => {
          onAdd({ name: value.trim(), kind, origin: "user" });
          setValue("");
        }}
      >
        Add
      </button>
    </div>
  );
}
