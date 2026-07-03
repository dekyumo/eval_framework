import { useState, useEffect } from 'react';

export function Registries() {
  const [activeTab, setActiveTab] = useState<'datasets' | 'tags' | 'rubrics' | 'extractors'>('extractors');
  const [extractors, setExtractors] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/registries/extractors')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setExtractors(data);
      })
      .catch(console.error);
  }, []);

  const handleSaveExtractor = async () => {
    try {
      const payload = {
        id: (document.getElementById('extractor_name') as HTMLInputElement).value || `ext_${Date.now()}`,
        name: (document.getElementById('extractor_name') as HTMLInputElement).value || `ext_${Date.now()}`,
        return_type: (document.getElementById('extractor_return_type') as HTMLSelectElement).value,
        python_code: (document.getElementById('extractor_python_code') as HTMLTextAreaElement).value,
        source_path: 'dummy.py',
        fingerprint: 'dummy_fingerprint',
        version: 1
      };
      await fetch('/api/registries/extractors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      // Refresh
      const res = await fetch('/api/registries/extractors');
      const data = await res.json();
      if (Array.isArray(data)) setExtractors(data);
    } catch(e) { console.error(e); }
  };

  const handleSaveRubric = async () => {
    try {
      const fieldTypeRaw = (document.getElementById('rubric_field_type') as HTMLSelectElement).value;
      let fieldType = fieldTypeRaw.toLowerCase();
      if (fieldType === 'boolean') fieldType = 'bool';
      if (fieldType === 'integer') fieldType = 'int';

      const payload = {
        id: (document.getElementById('rubric_name') as HTMLInputElement).value || `rubric_${Date.now()}`,
        name: (document.getElementById('rubric_name') as HTMLInputElement).value || `rubric_${Date.now()}`,
        instructions: (document.getElementById('rubric_instructions') as HTMLTextAreaElement).value || '',
        items: [{
          name: (document.getElementById('rubric_field_name') as HTMLInputElement).value || 'field',
          type: fieldType,
          description: ''
        }],
        default_judge_prompt: 'dummy prompt',
        fingerprint: 'dummy_fingerprint',
        version: 1,
        frozen: false
      };
      await fetch('/api/registries/rubrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch(e) { console.error(e); }
  };

  const handleSaveTag = async () => {
    try {
      const payload = {
        id: (document.getElementById('tag_name') as HTMLInputElement).value || `tag_${Date.now()}`,
        name: (document.getElementById('tag_name') as HTMLInputElement).value || `tag_${Date.now()}`,
        color: '#ccc'
      };
      await fetch('/api/registries/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch(e) { console.error(e); }
  };

  const handleSaveDataset = async () => {
    try {
      const payload = {
        id: (document.getElementById('dataset_name') as HTMLInputElement).value || `ds_${Date.now()}`,
        name: (document.getElementById('dataset_name') as HTMLInputElement).value || `ds_${Date.now()}`,
        case_ids: []
      };
      await fetch('/api/registries/datasets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch(e) { console.error(e); }
  };

  return (
    <div className="max-w-5xl mx-auto bg-surface-container rounded-xl border border-outline-variant h-full flex flex-col overflow-hidden text-on-surface">
      <div className="flex border-b border-outline-variant bg-surface-container-low p-2 gap-2">
        {['datasets', 'tags', 'rubrics', 'extractors'].map(tab => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            className={`px-4 py-2 text-sm font-bold capitalize rounded-md transition-colors ${activeTab === tab ? 'bg-surface-container-highest text-primary-fixed' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
          >
            {tab}
          </button>
        ))}
      </div>
      
      <div className="flex-1 p-6 overflow-y-auto">
        {activeTab === 'extractors' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold font-headline text-on-surface mb-4">Extractors</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="extractor_name" className="block text-sm font-semibold text-on-surface-variant mb-1">Name</label>
                <input id="extractor_name" className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed" placeholder="e.g. get_refund_amount" />
              </div>
              <div>
                <label htmlFor="extractor_return_type" className="block text-sm font-semibold text-on-surface-variant mb-1">Return Type</label>
                <select id="extractor_return_type" className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface focus:outline-none focus:border-primary-fixed">
                  <option>bool</option><option>int</option><option>float</option><option>enum</option>
                </select>
              </div>
            </div>
            
            <div>
              <label htmlFor="extractor_python_code" className="block text-sm font-semibold text-on-surface-variant mb-1">Python Code</label>
              <textarea 
                id="extractor_python_code"
                className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-4 font-mono text-sm h-64 text-on-surface focus:outline-none focus:border-primary-fixed" 
                defaultValue="def extract(trace):\n    return True" 
              />
            </div>
            
            <div className="flex justify-end gap-3 mt-4">
              <button className="px-4 py-2 border border-outline-variant rounded-md text-on-surface font-medium hover:bg-surface-container-highest transition-colors">
                Dry Run
              </button>
              <button 
                className="px-4 py-2 bg-primary-container text-on-primary-container rounded-md font-medium hover:bg-primary-fixed hover:text-white transition-colors"
                onClick={handleSaveExtractor}
              >
                Save Extractor
              </button>
            </div>
            
            <div className="mt-8 pt-8 border-t border-outline-variant">
              <h3 className="text-lg font-bold font-headline text-on-surface mb-4">Existing Extractors</h3>
              {extractors.length > 0 ? (
                <div className="space-y-2">
                  {extractors.map((e: any, i: number) => (
                    <div key={i} className="p-3 bg-surface-container-lowest border border-outline-variant rounded-md text-sm">
                      <span className="font-bold text-on-surface mr-2">{e.id}</span>
                      <span className="text-on-surface-variant uppercase text-xs font-mono">{e.return_type}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-on-surface-variant italic">No extractors found.</div>
              )}
            </div>
          </div>
        )}
        
        {activeTab === 'rubrics' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold font-headline text-on-surface mb-4">Rubrics</h2>
            <div>
              <label htmlFor="rubric_name" className="block text-sm font-semibold text-on-surface-variant mb-1">Rubric Name</label>
              <input id="rubric_name" className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed" placeholder="e.g. Tone Polite" />
            </div>
            <div>
              <label htmlFor="rubric_instructions" className="block text-sm font-semibold text-on-surface-variant mb-1">Instructions</label>
              <textarea id="rubric_instructions" className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 h-32 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed" placeholder="Instructions for the human or AI grader..." />
            </div>
            <div className="p-4 border border-outline-variant rounded-md bg-surface-container-low space-y-4">
              <h3 className="font-bold text-on-surface">Fields</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="rubric_field_name" className="block text-sm font-semibold text-on-surface-variant mb-1">Field Name</label>
                  <input id="rubric_field_name" className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed" placeholder="e.g. is_polite" />
                </div>
                <div>
                  <label htmlFor="rubric_field_type" className="block text-sm font-semibold text-on-surface-variant mb-1">Field Type</label>
                  <select id="rubric_field_type" className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface focus:outline-none focus:border-primary-fixed">
                    <option>Boolean</option><option>Integer</option><option>Float</option><option>Enum</option>
                  </select>
                </div>
              </div>
              <button className="px-3 py-1 bg-surface-container-highest border border-outline-variant rounded-md text-sm font-medium hover:bg-surface-variant transition-colors text-on-surface">
                + Add Field
              </button>
            </div>
            <div className="flex justify-end gap-3 mt-4">
              <button 
                className="px-4 py-2 bg-primary-container text-on-primary-container rounded-md font-medium hover:bg-primary-fixed hover:text-white transition-colors"
                onClick={handleSaveRubric}
              >
                Save Rubric
              </button>
            </div>
          </div>
        )}

        {activeTab === 'tags' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold font-headline text-on-surface mb-4">Tags</h2>
            <div>
              <label htmlFor="tag_name" className="block text-sm font-semibold text-on-surface-variant mb-1">Tag Name</label>
              <input id="tag_name" className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed" placeholder="e.g. pii-leak" />
            </div>
            <div className="flex justify-end gap-3 mt-4">
              <button 
                className="px-4 py-2 bg-primary-container text-on-primary-container rounded-md font-medium hover:bg-primary-fixed hover:text-white transition-colors"
                onClick={handleSaveTag}
              >
                Save Tag
              </button>
            </div>
          </div>
        )}

        {activeTab === 'datasets' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold font-headline text-on-surface mb-4">Datasets</h2>
            <div>
              <label htmlFor="dataset_name" className="block text-sm font-semibold text-on-surface-variant mb-1">Dataset Name</label>
              <input id="dataset_name" className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed" placeholder="e.g. Flight Booking Golden Set" />
            </div>
            <div className="flex justify-end gap-3 mt-4">
              <button 
                className="px-4 py-2 bg-primary-container text-on-primary-container rounded-md font-medium hover:bg-primary-fixed hover:text-white transition-colors"
                onClick={handleSaveDataset}
              >
                Save Dataset
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
