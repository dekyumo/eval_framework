import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { TaskProvider } from './context/TaskContext';
import { Layout } from './components/Layout';
import { Agents } from './pages/Agents';
import { ViewCases } from './pages/ViewCases';
import { CaseEditor } from './pages/CaseEditor';
import { Runs } from './pages/Runs';
import { Evals } from './pages/Evals';
import { Compare } from './pages/Compare';
import { Campaigns } from './pages/Campaigns';
import { Registries } from './pages/Registries';
import { HumanEval } from './pages/HumanEval';

export default function App() {
  return (
    <BrowserRouter>
      <TaskProvider>
        <Routes>
          <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/agents" replace />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/cases" element={<ViewCases />} />
          <Route path="/cases_editor" element={<CaseEditor />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/evals" element={<Evals />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/registries" element={<Registries />} />
          <Route path="/human-eval" element={<HumanEval />} />
        </Route>
        </Routes>
      </TaskProvider>
    </BrowserRouter>
  );
}
