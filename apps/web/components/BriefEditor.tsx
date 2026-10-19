"use client";

import { useState } from "react";
import { API_BASE, api, getToken } from "@/lib/api";
import { ErrorPanel } from "./ErrorPanel";
import type { BriefOut, BriefSectionOut } from "@/lib/types";

export function BriefEditor({
  brief,
  readOnly = false,
  onSaved,
}: {
  brief: BriefOut;
  readOnly?: boolean;
  onSaved?: (brief: BriefOut) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(brief.title);
  const [summary, setSummary] = useState(brief.summary);
  const [sections, setSections] = useState<BriefSectionOut[]>(brief.sections);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      const updated = await api.patch<BriefOut>(`/v1/briefs/${brief.id}`, {
        title,
        summary,
        sections,
      });
      onSaved?.(updated);
      setEditing(false);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  const updateSection = (index: number, body: string) => {
    setSections((current) =>
      current.map((section, i) => (i === index ? { ...section, body } : section)),
    );
  };

  const downloadMarkdown = async () => {
    try {
      const token = await getToken();
      const response = await fetch(`${API_BASE}/v1/briefs/${brief.id}/export.md`, {
        headers: { "X-Workspace-Token": token },
      });
      if (!response.ok) throw new Error("Export failed");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${brief.city}-brief.md`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err);
    }
  };

  return (
    <article className="card stack">
      <div className="spread">
        <div>
          {editing ? (
            <input className="input" value={title} onChange={(event) => setTitle(event.target.value)} maxLength={160} />
          ) : (
            <h3 className="headingSm">{title}</h3>
          )}
          <div className="row" style={{ gap: 6, marginTop: 6 }}>
            <span
              className={brief.source === "llm" ? "pill pillSky" : "pill"}
              title={
                brief.source === "llm"
                  ? "Written by the model from Qloo evidence"
                  : "Template brief — the LLM was unavailable, so this text is generated from Qloo evidence with fixed phrasing"
              }
            >
              {brief.source === "llm" ? "model-written" : "template"}
            </span>
            {brief.edited ? <span className="pill pillWarn">edited</span> : null}
            {brief.model ? <span className="pill">{brief.model}</span> : null}
          </div>
        </div>
        <div className="row" style={{ gap: 8 }}>
          <button type="button" className="btnOutline btnSmall" onClick={() => void downloadMarkdown()}>
            Export .md
          </button>
          {!readOnly ? (
            editing ? (
              <>
                <button type="button" className="btnText btnSmall" onClick={() => setEditing(false)}>
                  Cancel
                </button>
                <button type="button" className="btnPrimary btnSmall" disabled={busy} onClick={() => void save()}>
                  {busy ? "Saving…" : "Save"}
                </button>
              </>
            ) : (
              <button type="button" className="btnGhost btnSmall" onClick={() => setEditing(true)}>
                Edit
              </button>
            )
          ) : null}
        </div>
      </div>

      {error ? <ErrorPanel error={error} onRetry={() => void save()} /> : null}

      {editing ? (
        <textarea className="textarea" value={summary} maxLength={400} onChange={(event) => setSummary(event.target.value)} />
      ) : (
        <p className="serif">{summary}</p>
      )}

      <div className="stack">
        {sections.map((section, index) => (
          <div key={section.heading} className="stackSm">
            <h4 className="subheading">{section.heading}</h4>
            {editing ? (
              <textarea
                className="textarea"
                value={section.body}
                onChange={(event) => updateSection(index, event.target.value)}
              />
            ) : (
              <p>{section.body}</p>
            )}
            {section.cited_evidence_ids.length > 0 ? (
              <div className="row" style={{ gap: 4 }}>
                {section.cited_evidence_ids.map((id) => (
                  <span key={id} className="sourceChip" title={`Evidence ${id} — see the trace for the source Qloo call`}>
                    {id}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </article>
  );
}
