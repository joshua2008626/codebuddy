import { Link, useParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { WorkspaceView } from "./Workspace";
import { useRemoteWorkspace } from "../hooks/useRemoteWorkspace";

/** Route /projects/:id. Wrapped in ProtectedRoute; the server also checks that the project belongs to the person. */
export default function ProjectWorkspace() {
  const { id = "" } = useParams();
  // Keyed so that moving between projects always starts from a clean state.
  return <Loaded key={id} id={id} />;
}

function Loaded({ id }: { id: string }) {
  const { load, ...ws } = useRemoteWorkspace(id);

  if (load.status === "loading") {
    return (
      <>
        <Navbar />
        <p className="mx-auto mt-24 flex max-w-xl items-center gap-2 px-6 text-sm text-muted" role="status">
          <Loader2 size={16} className="animate-spin" aria-hidden /> Opening project…
        </p>
      </>
    );
  }
  if (load.status === "error") {
    return (
      <>
        <Navbar />
        <main className="mx-auto mt-20 max-w-xl px-6">
          <div role="alert" className="rounded-panel border border-danger/40 bg-danger/10 p-4 text-sm">
            <p className="font-medium text-danger">{load.notFound ? "Project not found" : "Couldn’t open the project"}</p>
            <p className="mt-1">{load.notFound ? "It may have been deleted, or it isn’t yours." : load.message}</p>
            <Link to="/projects" className="btn-ghost mt-3 inline-flex">Back to my projects</Link>
          </div>
        </main>
      </>
    );
  }
  return <WorkspaceView ws={ws} projectName={load.projectName} />;
}
