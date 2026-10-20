"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/#how", label: "How it works" },
  { href: "/analytics", label: "Analytics" },
  { href: "/sample", label: "Sample run" },
] as const;

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="siteHeader">
      <div className="headerInner">
        <Link href="/" className="brand" aria-label="TasteBound home">
          TasteBound
          <span className="brandDot" aria-hidden="true" />
        </Link>

        <nav className="navPill" aria-label="Main">
          {LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={active ? "navLink navLinkActive" : "navLink"}
                aria-current={active ? "page" : undefined}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="headerActions">
          <Link href="/start" className="btnPrimary">
            Start a run
          </Link>
        </div>
      </div>
    </header>
  );
}
