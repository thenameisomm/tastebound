"use client";

import { ApiError } from "@/lib/api";

export function ErrorPanel({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  let title = "Something went wrong";
  let detail = "";
  let code = "";
  if (error instanceof ApiError) {
    title = error.title;
    detail = error.detail;
    code = error.code;
  } else if (error instanceof Error) {
    detail = error.message;
  }
  return (
    <div className="banner bannerError" role="alert">
      <div className="stackSm" style={{ flex: 1 }}>
        <strong>{title}</strong>
        {detail ? <span>{detail}</span> : null}
        {code ? <span className="mono">code: {code}</span> : null}
      </div>
      {onRetry ? (
        <button type="button" className="btnOutline" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}
