import { Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import PhasePending from "./pages/PhasePending";
import Workspace from "./pages/Workspace";
import Practice from "./pages/Practice";
import ChallengePage from "./pages/ChallengePage";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Profile from "./pages/Profile";
import Learn from "./pages/Learn";
import LessonPage from "./pages/LessonPage";
import Projects from "./pages/Projects";
import ProjectWorkspace from "./pages/ProjectWorkspace";
import { ProtectedRoute } from "./components/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/workspace" element={<Workspace />} />
      <Route path="/practice" element={<Practice />} />
      <Route path="/practice/:id" element={<ChallengePage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
      <Route path="/projects" element={<ProtectedRoute><Projects /></ProtectedRoute>} />
      <Route path="/projects/:id" element={<ProtectedRoute><ProjectWorkspace /></ProtectedRoute>} />
      {/* Replaced by real pages in later phases. */}
      <Route path="/learn" element={<Learn />} />
      <Route path="/learn/:id" element={<LessonPage />} />
      <Route path="*" element={<PhasePending title="That page" phase={0} />} />
    </Routes>
  );
}
