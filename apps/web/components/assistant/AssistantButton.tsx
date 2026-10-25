"use client";

import { useAssistant, type AssistantOpenOptions } from "./AssistantContext";

export function AssistantButton({
  children = "Ask about this",
  prompt,
  focusMarketId,
  className = "btnOutline btnSmall",
}: {
  children?: React.ReactNode;
  prompt?: string;
  focusMarketId?: string;
  className?: string;
}) {
  const { open } = useAssistant();
  const options: AssistantOpenOptions = { prompt, focusMarketId };
  return (
    <button type="button" className={className} onClick={() => open(options)}>
      {children}
    </button>
  );
}
