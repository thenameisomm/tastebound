export function SourceChip({
  label,
  title,
  href,
}: {
  label: string;
  title?: string;
  href?: string;
}) {
  const content = <span className="sourceChip" title={title}>{label}</span>;
  if (!href) return content;
  return (
    <a href={href} target="_blank" rel="noreferrer">
      {content}
    </a>
  );
}
