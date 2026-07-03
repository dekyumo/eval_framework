import { useState, useEffect } from 'react';
import { ResultView } from '../components/ResultView';

export function Evals() {
  const [evalResults, setEvalResults] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/runs/scored')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setEvalResults(data);
      })
      .catch(console.error);
  }, []);
    const handleEvaluate = async () => {
      try {
        const runsRes = await fetch('/api/runs');
        const runs = await runsRes.json();
        
        for (const run of runs) {
          await fetch('/api/runs/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              run_id: run.id
            })
          });
        }
        
        // Refetch evals
        const evalsRes = await fetch('/api/runs/scored');
        const data = await evalsRes.json();
        if (Array.isArray(data)) {
          setEvalResults(data);
        }
      } catch (err) {
        console.error(err);
      }
    };

    return (
    <div className="max-w-6xl mx-auto flex h-full gap-6">
      <div className="w-1/3 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-200 bg-slate-50">
          <h2 className="text-lg font-bold text-slate-800">Run Evals</h2>
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
              onClick={handleEvaluate}
            >
              Run Evaluations
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {evalResults.length > 0 ? (
            evalResults.map((res: any, idx: number) => (
              <div key={idx} className="eval-item p-3 bg-white border border-slate-200 rounded-md cursor-pointer hover:border-indigo-300">
                <div className="text-sm font-medium text-slate-800 truncate">{res.run_id}</div>
              </div>
            ))
          ) : (
            <div className="p-4 text-center text-sm text-slate-500 italic">No scored runs available.</div>
          )}
        </div>
      </div>

      <div className="flex-1 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col p-6">
        <h2 className="text-xl font-bold text-slate-800 mb-6">Evaluation Results</h2>
        
        <div className="space-y-6">
          {evalResults.length > 0 ? (
            evalResults.map((res, i) => (
              <div key={i} className="p-4 border border-slate-200 rounded-lg">
                 {/* render logic */}
              </div>
            ))
          ) : (
            <div className="text-slate-500 text-sm italic">Select a run to view its evaluation results.</div>
          )}
        </div>
      </div>
    </div>
  );
}
