import { useRef } from "react";

interface Props {
  /** "vertical" is a vertical bar you drag left/right; "horizontal" is a horizontal bar you drag up/down. */
  direction: "vertical" | "horizontal";
  label: string;
  /** Called with the pixel movement since the last event. Positive means right or down. */
  onResize: (delta: number) => void;
}

/** Draggable and keyboard-operable divider between panels. */
export function ResizeHandle({ direction, label, onResize }: Props) {
  const dragging = useRef(false);
  const vertical = direction === "vertical";

  return (
    <div
      role="separator"
      aria-orientation={vertical ? "vertical" : "horizontal"}
      aria-label={label}
      tabIndex={0}
      className={`group relative hidden shrink-0 lg:block ${vertical ? "w-1 cursor-col-resize" : "h-1 cursor-row-resize"}`}
      onPointerDown={(e) => {
        dragging.current = true;
        e.currentTarget.setPointerCapture(e.pointerId);
      }}
      onPointerMove={(e) => {
        if (dragging.current) onResize(vertical ? e.movementX : e.movementY);
      }}
      onPointerUp={(e) => {
        dragging.current = false;
        e.currentTarget.releasePointerCapture(e.pointerId);
      }}
      onKeyDown={(e) => {
        const step = e.shiftKey ? 48 : 16;
        if (vertical && e.key === "ArrowLeft") onResize(-step);
        if (vertical && e.key === "ArrowRight") onResize(step);
        if (!vertical && e.key === "ArrowUp") onResize(-step);
        if (!vertical && e.key === "ArrowDown") onResize(step);
      }}
    >
      {/* Visible line that brightens on hover/focus/drag. */}
      <span className={`absolute bg-line transition-colors group-hover:bg-volt group-focus-visible:bg-cyan ${vertical ? "inset-y-0 left-0 w-px" : "inset-x-0 top-0 h-px"}`} />
    </div>
  );
}
