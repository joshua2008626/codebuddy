/**
 * Site-wide constants.
 * Replace the social URLs with your real profiles before deploying.
 */
export const SITE = {
  name: "CodeBuddy",
  tagline: "Write it, run it, understand it.",
  social: [
    { label: "GitHub", href: "https://github.com" },
    { label: "X", href: "https://x.com" },
    { label: "LinkedIn", href: "https://www.linkedin.com" },
  ],
} as const;

/** Primary navigation. Routes for later phases show an honest "not built yet" page until then. */
export const NAV = [
  { label: "Features", href: "/#features" },
  { label: "Workspace", href: "/workspace" },
  { label: "Projects", href: "/projects" },
  { label: "Practice", href: "/practice" },
  { label: "Learn", href: "/learn" },
] as const;
