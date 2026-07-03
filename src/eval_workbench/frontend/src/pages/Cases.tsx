import { useState, useEffect } from 'react';
import { SplitBadge } from '../components/SplitBadge';

export function Cases() {
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch from backend
    fetch('/api/cases')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setCases(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

    const handleSaveCase = async () => {
      try {
        const payload = {
          id: `case_${Date.now()}`,
          name: (document.getElementById('case_name') as HTMLInputElement).value || 'Unnamed Case',
          dataset_id: (document.getElementById('case_dataset') as HTMLSelectElement).value,
          domain_position: (document.getElementById('case_domain_position') as HTMLSelectElement).value as any,
          problem_type: (document.getElementById('case_problem_type') as HTMLSelectElement).value as any,
          split: (document.getElementById('case_split') as HTMLSelectElement).value as any,
          target_agent_path: 'a_single_agent.day_trip:root_agent',
          conversation: [{role: 'user', kind: 'text', text: 'dummy'}], // Minimal conversation
          expected_rubrics: [],
          expected_extractors: [],
          tag_ids: [],
          fault_ids: []
        };
        await fetch('/api/cases/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        
        // Refresh
        const res = await fetch('/api/cases');
        const data = await res.json();
        if (Array.isArray(data)) setCases(data);
      } catch (e) {
        console.error(e);
      }
    };

    return (
      <div className="max-w-6xl mx-auto flex h-full gap-6">
      {/* List / Matrix Pane */}
      <div className="w-1/3 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-200 bg-slate-50">
          <h2 className="text-lg font-bold text-slate-800">Cases & Evals</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {cases.map(c => (
            <div key={c.id} className="p-3 rounded-md hover:bg-slate-50 cursor-pointer border border-transparent hover:border-slate-200">
              <div className="font-medium text-slate-800 mb-1">{c.name}</div>
              <div className="flex flex-wrap items-center gap-2 mt-2">
                <SplitBadge split={c.split} />
                <span className="text-xs text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">{c.domain_position} • {c.problem_type}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Editor Pane */}
      <div className="flex-1 bg-white rounded-xl shadow-sm border border-slate-200 p-6 overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-slate-800">Edit Case</h2>
          <button className="new-case-btn bg-indigo-50 text-indigo-600 font-medium py-1.5 px-4 rounded-md shadow-sm transition-colors border border-indigo-200 hover:bg-indigo-100">
            New Case
          </button>
        </div>
        
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="case_name" className="block text-sm font-semibold text-slate-700 mb-1">Case Name</label>
              <input id="case_name" className="w-full border border-slate-300 rounded-md p-2" defaultValue="Refund request" />
            </div>
            <div>
              <label htmlFor="case_dataset" className="block text-sm font-semibold text-slate-700 mb-1">Dataset</label>
              <select id="case_dataset" className="w-full border border-slate-300 rounded-md p-2">
                <option>DayTrip Tests</option>
                <option>default_dataset</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label htmlFor="case_domain_position" className="block text-sm font-semibold text-slate-700 mb-1">Domain Position</label>
              <select id="case_domain_position" className="w-full border border-slate-300 rounded-md p-2">
                <option>in</option><option>margin</option><option>ood</option>
              </select>
            </div>
            <div>
              <label htmlFor="case_problem_type" className="block text-sm font-semibold text-slate-700 mb-1">Problem Type</label>
              <select id="case_problem_type" className="w-full border border-slate-300 rounded-md p-2">
                <option>happy</option><option>technical</option><option>adversarial</option><option>client</option>
              </select>
            </div>
            <div>
              <label htmlFor="case_split" className="block text-sm font-semibold text-slate-700 mb-1">Split</label>
              <select id="case_split" className="w-full border border-slate-300 rounded-md p-2">
                <option>judging</option><option>optimisation</option>
              </select>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-200">
            <h3 className="font-bold text-slate-800 mb-3">Conversation Builder</h3>
            <div className="bg-slate-50 border border-slate-200 rounded-md p-4 space-y-4">
              <div className="flex gap-3">
                <select className="border border-slate-300 rounded-md p-2 text-sm w-32 bg-white">
                  <option>user</option><option>assistant</option>
                </select>
                <textarea className="flex-1 border border-slate-300 rounded-md p-2 text-sm h-20" defaultValue="Hello, I want a refund." />
                <button className="text-red-500 hover:text-red-700 font-bold px-2">×</button>
              </div>
              <button className="text-sm text-indigo-600 font-bold hover:underline">+ Add Turn</button>
            </div>
          </div>

          <button 
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2.5 px-6 rounded-md shadow-sm transition-colors"
            onClick={handleSaveCase}
          >
            Save Case
          </button>
        </div>
      </div>
    </div>
  );
}
