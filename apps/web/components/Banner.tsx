export function Banner({
  tone = "info",
  children,
}: {
  tone?: "info" | "warn" | "error";
  children: React.ReactNode;
}) {
  const className =
    tone === "error" ? "banner bannerError" : tone === "warn" ? "banner bannerWarn" : "banner bannerInfo";
  return <div className={className}>{children}</div>;
}
