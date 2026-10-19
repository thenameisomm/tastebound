export function EmptyState({
  title,
  children,
}: {
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="empty">
      <p className="subheading">{title}</p>
      {children ? <p className="muted" style={{ marginTop: 8 }}>{children}</p> : null}
    </div>
  );
}
