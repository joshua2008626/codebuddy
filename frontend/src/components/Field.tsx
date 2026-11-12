import { useId, type InputHTMLAttributes } from "react";

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, "id"> {
  label: string;
  error?: string | null;
  hint?: string;
}

/** Labelled input. The error and hint are announced with the field, and the field is marked invalid for screen readers. */
export function Field({ label, error, hint, ...input }: Props) {
  const id = useId();
  const described = [error ? `${id}-err` : null, hint ? `${id}-hint` : null].filter(Boolean).join(" ") || undefined;
  return (
    <div>
      <label htmlFor={id} className="text-sm font-medium">{label}</label>
      <input
        {...input}
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={described}
        className={`mt-1.5 w-full rounded-chip border bg-ink/60 px-3 py-2 text-sm ${error ? "border-danger" : "border-line"}`}
      />
      {hint && <p id={`${id}-hint`} className="mt-1 text-xs text-muted">{hint}</p>}
      {error && <p id={`${id}-err`} className="mt-1 text-xs text-danger">{error}</p>}
    </div>
  );
}
