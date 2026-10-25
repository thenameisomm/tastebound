"use client";

import { createContext, useContext } from "react";

export type AssistantOpenOptions = {
  prompt?: string;
  focusMarketId?: string;
};

export type AssistantController = {
  open: (options?: AssistantOpenOptions) => void;
  close: () => void;
  isOpen: boolean;
};

export const AssistantContext = createContext<AssistantController | null>(null);

export function useAssistant(): AssistantController {
  const value = useContext(AssistantContext);
  if (!value) {
    throw new Error("useAssistant must be used inside AssistantProvider");
  }
  return value;
}
