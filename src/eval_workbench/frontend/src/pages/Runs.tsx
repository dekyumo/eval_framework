import { useState, useEffect } from 'react';
import { TraceView } from '../components/TraceView';

export function Runs() {
  const [traces, setTraces] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/runs')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setTraces(data.map(run => run.trace));
        }
      })
      .catch(console.error);
  }, []);

    const handleGenerate = async () => {
      // In a real implementation, the backend would handle the loop over dataset cases.
      // Here, we fetch cases, and generate a run for the first one found (or all of them)
      try {
        const casesRes = await fetch('/api/cases');
        const cases = await casesRes.json();
        const datasetCases = cases.filter((c: any) => c.dataset_id === 'DayTrip Tests' || true); // simplify for now
        
        for (const c of datasetCases) {
          await fetch('/api/runs/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              snapshot_id: 'HEAD:a_single_agent.day_trip:root_agent',
              case_id: c.id,
              model_id: 'gemini-2.5-flash'
            })
          });
        }
        
        // Refetch traces
        const runsRes = await fetch('/api/runs');
        const data = await runsRes.json();
        if (Array.isArray(data)) {
          setTraces(data.map((run: any) => run.trace));
        }
      } catch (err) {
        console.error(err);
      }
    };

    return (
    <div className="max-w-6xl mx-auto flex h-full gap-6">
      <div className="w-1/3 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-200 bg-slate-50">
          <h2 className="text-lg font-bold text-slate-800">Run Generation</h2>
          <div className="mt-3 space-y-2">
            <select aria-label="Snapshot" className="w-full border border-slate-300 rounded p-1.5 text-sm">
              <option>Select Snapshot...</option>
              <option>HEAD:a_single_agent.day_trip:root_agent</option>
            </select>
            <select aria-label="Dataset" className="w-full border border-slate-300 rounded p-1.5 text-sm">
              <option>Select Dataset...</option>
              <option>DayTrip Tests</option>
            </select>
            <button 
              className="w-full bg-indigo-600 text-white font-medium py-1.5 rounded text-sm hover:bg-indigo-700"
              onClick={handleGenerate}
              id="generate-traces-btn"
            >
              Generate Traces
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {traces.length > 0 ? (
            traces.map((trace: any) => (
              <div key={trace.id} className="trace-item p-3 bg-indigo-50 border border-indigo-100 rounded-md cursor-pointer mb-2">
                <div className="text-sm font-medium text-indigo-900 truncate">{trace.id}</div>
                <div className="text-xs text-indigo-600 mt-1">{trace.latency_ms || 0}ms</div>
              </div>
            ))
          ) : (
            <div className="p-4 text-center text-sm text-slate-500 italic">No traces available.</div>
          )}
        </div>
      </div>

      <div className="flex-1 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
          <h2 className="text-lg font-bold text-slate-800">Trace Detail</h2>
          <button className="px-3 py-1 bg-white border border-slate-300 rounded text-sm font-medium text-slate-700 hover:bg-slate-50">
            Rerun
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          {traces.length > 0 ? (
            <TraceView trace={traces[0]} />
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500 text-sm">No trace selected</div>
          )}
        </div>
      </div>
    </div>
  );
}
