import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Agents } from './pages/Agents';
import { Cases } from './pages/Cases';
import { Runs } from './pages/Runs';
import { Evals } from './pages/Evals';
import { Compare } from './pages/Compare';
import { Campaigns } from './pages/Campaigns';
import { Registries } from './pages/Registries';
import { HumanEval } from './pages/HumanEval';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/agents" replace />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/evals" element={<Evals />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/registries" element={<Registries />} />
          <Route path="/human-eval" element={<HumanEval />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
