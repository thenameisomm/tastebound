"use client";

export function AssistantLauncher({
  onClick,
  visible,
}: {
  onClick: () => void;
  visible: boolean;
}) {
  if (!visible) return null;
  return (
    <button
      type="button"
      className="assistantLauncher"
      onClick={onClick}
      data-assistant-launcher
      aria-haspopup="dialog"
    >
      <span className="assistantLauncherDot" aria-hidden="true" />
      Ask TasteBound
    </button>
  );
}
