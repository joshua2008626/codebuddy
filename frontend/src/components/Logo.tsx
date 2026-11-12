import { useId } from "react";

/**
 * CodeBuddy mark: two brackets leaning toward each other with a cyan cursor dot between them.
 * Read together they form a face; the dot is the "buddy" sitting inside your code.
 */
export function LogoMark({ size = 32 }: { size?: number }) {
  // Unique gradient id so multiple logos on one page do not collide.
  // useId() returns ids containing colons, which can break url(#id) references, so strip them.
  const gid = `cb-grad-${useId().replace(/:/g, "")}`;
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="rgb(var(--c-blue))" />
          <stop offset="1" stopColor="rgb(var(--c-violet))" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="16" fill="rgb(var(--c-panel))" />
      <rect x="0.75" y="0.75" width="62.5" height="62.5" rx="15.25" fill="none" stroke="rgb(var(--c-line))" strokeWidth="1.5" />
      <path d="M25 19 12 32l13 13" fill="none" stroke={`url(#${gid})`} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M39 19l13 13-13 13" fill="none" stroke={`url(#${gid})`} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="32" cy="32" r="4.5" fill="rgb(var(--c-cyan))" />
    </svg>
  );
}

export function Logo({ size = 32 }: { size?: number }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <LogoMark size={size} />
      <span className="text-lg font-semibold tracking-tight">CodeBuddy</span>
    </span>
  );
}
