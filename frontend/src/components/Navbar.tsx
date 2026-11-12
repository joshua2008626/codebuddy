import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, Moon, Sun, X } from "lucide-react";
import { Logo } from "./Logo";
import { NAV } from "../config/site";
import { useTheme } from "../lib/theme";
import { useAuth } from "../hooks/useAuth";

/** Hash links (/#features) use a plain anchor so the browser handles the scroll. */
function NavItem({ href, label, onClick }: { href: string; label: string; onClick?: () => void }) {
  const cls = "rounded-chip px-3 py-2 text-sm text-muted transition-colors hover:text-fg";
  return href.includes("#") ? (
    <a href={href} className={cls} onClick={onClick}>{label}</a>
  ) : (
    <Link to={href} className={cls} onClick={onClick}>{label}</Link>
  );
}

export function Navbar() {
  const [open, setOpen] = useState(false);
  const { theme, toggle } = useTheme();
  const { user, logout } = useAuth();
  const [logoutError, setLogoutError] = useState<string | null>(null);

  async function doLogout() {
    setOpen(false);
    setLogoutError(await logout());
  }

  return (
    <header className="sticky top-0 z-40 border-b border-line/70 bg-ink/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
        <Link to="/" aria-label="CodeBuddy home"><Logo /></Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
          {NAV.map((n) => <NavItem key={n.label} {...n} />)}
        </nav>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggle}
            className="btn-ghost !px-2.5"
            aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          >
            {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          {user ? (
            <>
              <Link to="/profile" className="hidden max-w-[10rem] truncate px-3 py-2 text-sm text-muted hover:text-fg sm:inline" title="Your profile">{user.display_name}</Link>
              <button type="button" onClick={doLogout} className="hidden px-3 py-2 text-sm text-muted hover:text-fg sm:inline">Log out</button>
            </>
          ) : (
            <Link to="/login" className="hidden px-3 py-2 text-sm text-muted hover:text-fg sm:inline">Log in</Link>
          )}
          <Link to="/workspace" className="btn-primary hidden sm:inline-flex">Start coding</Link>
          <button
            type="button"
            className="btn-ghost !px-2.5 md:hidden"
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </div>

      {logoutError && <p role="alert" className="border-t border-danger/40 bg-danger/10 px-5 py-2 text-center text-sm text-danger">{logoutError}</p>}

      {open && (
        <nav id="mobile-nav" className="border-t border-line bg-panel px-5 py-3 md:hidden" aria-label="Mobile">
          <div className="flex flex-col">
            {NAV.map((n) => <NavItem key={n.label} {...n} onClick={() => setOpen(false)} />)}
            {user ? (
              <>
                <Link to="/profile" className="rounded-chip px-3 py-2 text-sm text-muted hover:text-fg" onClick={() => setOpen(false)}>Profile ({user.display_name})</Link>
                <button type="button" className="rounded-chip px-3 py-2 text-left text-sm text-muted hover:text-fg" onClick={doLogout}>Log out</button>
              </>
            ) : (
              <Link to="/login" className="rounded-chip px-3 py-2 text-sm text-muted hover:text-fg" onClick={() => setOpen(false)}>Log in</Link>
            )}
            <Link to="/workspace" className="btn-primary mt-2" onClick={() => setOpen(false)}>Start coding</Link>
          </div>
        </nav>
      )}
    </header>
  );
}
