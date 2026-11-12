import { Link } from "react-router-dom";
import { Navbar } from "../components/Navbar";
import { Hero } from "../components/Hero";
import { Features } from "../components/Features";
import { WorkspacePreview } from "../components/WorkspacePreview";
import { DemoStats } from "../components/DemoStats";
import { Footer } from "../components/Footer";

export default function Landing() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <DemoStats />
        <Features />
        <WorkspacePreview />

        <section className="mx-auto max-w-6xl px-5 pb-24">
          <div className="panel flex flex-col items-start gap-5 p-8 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight">Open a file and start typing</h2>
              <p className="mt-1 text-muted">No setup. Pick a language and run your first program.</p>
            </div>
            <Link to="/workspace" className="btn-primary !px-5 !py-3">Start Coding</Link>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
