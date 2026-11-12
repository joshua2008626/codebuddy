import { Link } from "react-router-dom";
import { Logo } from "./Logo";
import { NAV, SITE } from "../config/site";

export function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-12 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <Logo />
          <p className="mt-3 max-w-xs text-sm text-muted">{SITE.tagline} A coding workspace for C, Python and Java, with an AI buddy beside you.</p>
        </div>

        <nav aria-label="Footer">
          <h2 className="text-sm font-semibold">Product</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            {NAV.map((n) => (
              <li key={n.label}>
                {n.href.includes("#") ? (
                  <a className="hover:text-fg" href={n.href}>{n.label}</a>
                ) : (
                  <Link className="hover:text-fg" to={n.href}>{n.label}</Link>
                )}
              </li>
            ))}
          </ul>
        </nav>

        <div>
          <h2 className="text-sm font-semibold">Follow</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            {SITE.social.map((s) => (
              <li key={s.label}>
                <a className="hover:text-fg" href={s.href} target="_blank" rel="noopener noreferrer">{s.label}</a>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="border-t border-line py-5 text-center text-xs text-muted">
        © {new Date().getFullYear()} CodeBuddy. Built as a learning project.
      </div>
    </footer>
  );
}
