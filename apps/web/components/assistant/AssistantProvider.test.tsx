import type { ReactNode } from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";
import type {
  AssistantAnswer,
  AssistantBootstrap,
  AssistantConversation,
} from "@/lib/types";
import { AssistantButton } from "./AssistantButton";
import { AssistantProvider } from "./AssistantProvider";

const { getMock, postMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
}));

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      get: getMock,
      post: postMock,
    },
  };
});

vi.mock("next/navigation", () => ({
  usePathname: () => "/runs/demo-e5b2b8fd/markets/co-cartagena",
}));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

const RUN_ID = "demo-e5b2b8fd";
const FOCUS_ID = "co-cartagena";

const bootstrap: AssistantBootstrap = {
  enabled: true,
  ready: true,
  model: "fake-1",
  focus_market_id: FOCUS_ID,
  suggested_questions: [
    "Explain Cartagena's taste score and confidence.",
    "Who is the audience in Cartagena?",
  ],
  notice: null,
  max_message_chars: 800,
  conversation_ttl_minutes: 60,
};

const conversation: AssistantConversation = {
  conversation_id: "conversation-1",
  run_id: RUN_ID,
  focus_market_id: FOCUS_ID,
  messages: [],
  created_at: "2026-10-25T09:00:00Z",
  updated_at: "2026-10-25T09:00:00Z",
};

const answer: AssistantAnswer = {
  conversation_id: "conversation-1",
  message_id: "message-1",
  answer:
    "Cartagena leads this run with a taste score of 99.26 and a gap of 98.17 points. Taste fit is not a visitor forecast.",
  evidence: [
    {
      id: "E1",
      kind: "market_score",
      label: "Cartagena score",
      detail: "rank 1 · taste 99.26 · gap 98.17 points · quadrant untapped",
      href: `/runs/${RUN_ID}/markets/${FOCUS_ID}#score`,
      source_call_id: "call-1",
    },
  ],
  followups: ["What should we lead with in Cartagena?"],
  model: "fake-1",
  created_at: "2026-10-25T09:01:00Z",
};

function conversationResponse(payload = conversation) {
  postMock.mockImplementation((path: string) => {
    if (path.endsWith("/conversations")) return Promise.resolve(payload);
    return Promise.resolve(answer);
  });
}

describe("Results assistant", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    getMock.mockReset();
    postMock.mockReset();
    getMock.mockResolvedValue(bootstrap);
  });

  it("opens from a contextual action, answers with evidence and reuses the conversation", async () => {
    const user = userEvent.setup();
    conversationResponse();
    postMock
      .mockResolvedValueOnce(conversation)
      .mockResolvedValueOnce(answer)
      .mockResolvedValueOnce({
        ...answer,
        message_id: "message-2",
        answer: "Lead with the untapped score, then check the audience caveat.",
        evidence: [answer.evidence[0]!],
        followups: [],
      });

    render(
      <AssistantProvider>
        <AssistantButton prompt="Explain this market.">
          Ask about this market
        </AssistantButton>
      </AssistantProvider>,
    );

    await user.click(
      screen.getByRole("button", { name: "Ask about this market" }),
    );
    const dialog = await screen.findByRole("dialog");
    expect(
      await within(dialog).findByText(/Cartagena leads this run/),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByRole("link", { name: /E1.*Cartagena score/i }),
    ).toHaveAttribute("href", `/runs/${RUN_ID}/markets/${FOCUS_ID}#score`);
    expect(
      window.sessionStorage.getItem(`tb_assistant_conversation:${RUN_ID}`),
    ).toBe("conversation-1");
    expect(postMock).toHaveBeenNthCalledWith(
      1,
      `/v1/runs/${RUN_ID}/assistant/conversations`,
      { focus_market_id: FOCUS_ID },
    );
    expect(postMock).toHaveBeenNthCalledWith(
      2,
      `/v1/runs/${RUN_ID}/assistant/conversations/conversation-1/messages`,
      { message: "Explain this market.", focus_market_id: FOCUS_ID },
    );

    await user.click(
      within(dialog).getByRole("button", {
        name: "What should we lead with in Cartagena?",
      }),
    );
    expect(
      await within(dialog).findByText(/Lead with the untapped score/),
    ).toBeInTheDocument();
    expect(postMock).toHaveBeenNthCalledWith(
      3,
      `/v1/runs/${RUN_ID}/assistant/conversations/conversation-1/messages`,
      {
        message: "What should we lead with in Cartagena?",
        focus_market_id: FOCUS_ID,
      },
    );

    await user.click(
      within(dialog).getByRole("button", { name: "Close results assistant" }),
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows an honest unavailable state when no model is configured", async () => {
    const user = userEvent.setup();
    getMock.mockResolvedValue({
      ...bootstrap,
      enabled: false,
      ready: false,
      model: null,
      notice: "The results assistant needs a configured model provider.",
    } satisfies AssistantBootstrap);

    render(
      <AssistantProvider>
        <AssistantButton prompt="Explain this market.">
          Ask about this market
        </AssistantButton>
      </AssistantProvider>,
    );

    await user.click(
      screen.getByRole("button", { name: "Ask about this market" }),
    );
    const dialog = await screen.findByRole("dialog");
    expect(
      await within(dialog).findByText("No model configured"),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByText(
        "The results assistant needs a configured model provider.",
      ),
    ).toBeInTheDocument();
    expect(
      within(dialog).queryByLabelText("Ask a question about this run"),
    ).not.toBeInTheDocument();
    expect(postMock).not.toHaveBeenCalled();
  });

  it("restores a stored conversation when the drawer opens", async () => {
    const user = userEvent.setup();
    window.sessionStorage.setItem(
      `tb_assistant_conversation:${RUN_ID}`,
      "conversation-1",
    );
    getMock.mockImplementation((path: string) => {
      if (path.includes("/conversations/")) {
        return Promise.resolve({
          ...conversation,
          messages: [
            {
              id: "old-question",
              role: "user",
              content: "What stands out?",
              evidence: [],
              created_at: "2026-10-25T08:00:00Z",
            },
            {
              id: "old-answer",
              role: "assistant",
              content: "The untapped gap is the clearest signal.",
              evidence: [answer.evidence[0]!],
              created_at: "2026-10-25T08:01:00Z",
            },
          ],
        } satisfies AssistantConversation);
      }
      return Promise.resolve(bootstrap);
    });

    render(
      <AssistantProvider>
        <p>Results page</p>
      </AssistantProvider>,
    );

    await user.click(screen.getByRole("button", { name: "Ask TasteBound" }));
    const dialog = await screen.findByRole("dialog");
    expect(
      await within(dialog).findByText(
        "The untapped gap is the clearest signal.",
      ),
    ).toBeInTheDocument();
    expect(postMock).not.toHaveBeenCalled();
  });

  it("clears an expired conversation and restores the new question", async () => {
    const user = userEvent.setup();
    window.sessionStorage.setItem(
      `tb_assistant_conversation:${RUN_ID}`,
      "conversation-1",
    );
    getMock.mockImplementation((path: string) => {
      if (path.includes("/conversations/")) {
        return Promise.resolve({
          ...conversation,
          messages: [
            {
              id: "old-answer",
              role: "assistant",
              content: "The untapped gap is the clearest signal.",
              evidence: [answer.evidence[0]!],
              created_at: "2026-10-25T08:01:00Z",
            },
          ],
        } satisfies AssistantConversation);
      }
      return Promise.resolve(bootstrap);
    });
    postMock.mockRejectedValueOnce(
      new ApiError(
        404,
        "conversation_not_found",
        "Conversation not found",
        "This conversation no longer exists.",
      ),
    );

    render(
      <AssistantProvider>
        <p>Results page</p>
      </AssistantProvider>,
    );

    await user.click(screen.getByRole("button", { name: "Ask TasteBound" }));
    const dialog = await screen.findByRole("dialog");
    expect(
      await within(dialog).findByText(
        "The untapped gap is the clearest signal.",
      ),
    ).toBeInTheDocument();

    await user.type(
      within(dialog).getByLabelText("Ask a question about this run"),
      "What changed?",
    );
    await user.click(within(dialog).getByRole("button", { name: "Send" }));
    expect(
      await within(dialog).findByText("Could not answer"),
    ).toBeInTheDocument();
    expect(
      within(dialog).queryByText("The untapped gap is the clearest signal."),
    ).not.toBeInTheDocument();
    expect(
      within(dialog).getByLabelText("Ask a question about this run"),
    ).toHaveValue("What changed?");
    expect(
      window.sessionStorage.getItem(`tb_assistant_conversation:${RUN_ID}`),
    ).toBeNull();
  });

  it("removes a failed optimistic question and restores the input", async () => {
    const user = userEvent.setup();
    postMock
      .mockResolvedValueOnce(conversation)
      .mockRejectedValueOnce(
        new ApiError(
          502,
          "assistant_ungrounded",
          "Assistant answer not grounded",
          "The answer could not be verified against this run's data.",
        ),
      );

    render(
      <AssistantProvider>
        <AssistantButton prompt="Explain this market.">
          Ask about this market
        </AssistantButton>
      </AssistantProvider>,
    );

    await user.click(
      screen.getByRole("button", { name: "Ask about this market" }),
    );
    const dialog = await screen.findByRole("dialog");
    expect(
      await within(dialog).findByText("Could not answer"),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByText(/could not be verified against this run/),
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(
        within(dialog).getByLabelText("Ask a question about this run"),
      ).toHaveValue("Explain this market."),
    );
    expect(
      within(dialog).queryByText("Explain this market.", {
        selector: ".assistantMessageText",
      }),
    ).not.toBeInTheDocument();
  });
});
