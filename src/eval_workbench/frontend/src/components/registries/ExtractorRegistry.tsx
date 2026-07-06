import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { Select } from '../ui/Select';
import { TextAreaWithLabel } from '../ui/Textarea';
import { AgentPromptInput } from '../ui/AgentPromptInput';
import { Heading, Text, FormLabel } from '../ui/Typography';
import { BorderedSection } from '../ui/PageLayout';

interface Extractor {
  id: string;
  name: string;
  return_type: string;
  python_code?: string;
}

interface ExtractorRegistryProps {
  extractors: Extractor[];
  onFetchAll: () => void;
}

export function ExtractorRegistry({ extractors, onFetchAll }: ExtractorRegistryProps) {
  const [extName, setExtName] = useState('');
  const [extReturnType, setExtReturnType] = useState('bool');
  const [extPythonCode, setExtPythonCode] = useState('def extract(trace):\n    return True');
  const [extAgentPrompt, setExtAgentPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedExtId, setSelectedExtId] = useState<string | null>(null);

  const handleGenerateExtractorCode = async () => {
    if (!extAgentPrompt.trim()) return;
    setIsGenerating(true);
    try {
      const res = await fetch('/api/registries/extractors/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: extAgentPrompt })
      });
      const data = await res.json();
      if (data.code) {
        setExtPythonCode(data.code);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveExtractor = async () => {
    if (!extName) return;
    try {
      const payload = {
        id: selectedExtId || `ext_${crypto.randomUUID().substring(0, 8)}`,
        name: extName,
        return_type: extReturnType,
        python_code: extPythonCode,
        source_path: 'local_ui.py',
        fingerprint: 'local_edit',
        version: 1
      };
      await fetch('/api/registries/extractors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      setExtName('');
      setExtPythonCode('def extract(trace):\n    return True');
      setSelectedExtId(null);
      onFetchAll();
    } catch(e) { console.error(e); }
  };

  const handleDeleteExtractor = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await fetch(`/api/registries/extractors/${id}`, { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error || "Failed to delete extractor");
        return;
      }
      onFetchAll();
    } catch(e) { console.error(e); }
  };

  return (
    <div className="space-y-6 text-on-surface">
      <Heading level={2} className="mb-4">Extractors</Heading>
      
      {/* AGENT Generator Section */}
      <AgentPromptInput
        title="Ask Assistant Agent to write extraction logic"
        placeholder="e.g. Find the last dollar value in the trace and convert it to float"
        value={extAgentPrompt}
        onChange={setExtAgentPrompt}
        onSubmit={handleGenerateExtractorCode}
        isLoading={isGenerating}
        submitLabel="Generate Code"
        inputAriaLabel="Extractor generation prompt"
      />

      <div className="grid grid-cols-2 gap-4">
        <div>
          <FormLabel htmlFor="extractor_name">Name</FormLabel>
          <input 
            id="extractor_name" 
            value={extName}
            onChange={e => setExtName(e.target.value)}
            className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed text-sm" 
            placeholder="e.g. get_refund_amount" 
          />
        </div>
        <div>
          <FormLabel htmlFor="extractor_return_type">Return Type</FormLabel>
          <Select 
            id="extractor_return_type" 
            value={extReturnType}
            onChange={e => setExtReturnType(e.target.value)}
          >
            <option value="bool">bool</option>
            <option value="int">int</option>
            <option value="float">float</option>
            <option value="enum">enum</option>
          </Select>
        </div>
      </div>
      
      <TextAreaWithLabel
        id="extractor_python_code"
        label="Python Code"
        value={extPythonCode}
        onChange={e => setExtPythonCode(e.target.value)}
        className="font-mono text-sm h-64"
      />
      
      <div className="flex justify-end gap-3 mt-4">
        {selectedExtId && (
          <Button 
            variant="normal"
            className="mr-auto"
            onClick={() => {
              setSelectedExtId(null);
              setExtName('');
              setExtPythonCode('def extract(trace):\n    return True');
            }}
          >
            Cancel Edit
          </Button>
        )}
        <Button 
          variant="cta"
          onClick={handleSaveExtractor}
        >
          {selectedExtId ? 'Update Extractor' : 'Save Extractor'}
        </Button>
      </div>
      
      <BorderedSection position="top" className="space-y-4">
        <Heading level={3}>Existing Extractors</Heading>
        {extractors.length > 0 ? (
          <div className="space-y-2">
            {extractors.map((e) => (
              <BorderedSection 
                key={e.id} 
                data-testid={`extractor-item-${e.name}`}
                onClick={() => {
                  setSelectedExtId(e.id);
                  setExtName(e.name);
                  setExtReturnType(e.return_type);
                  setExtPythonCode(e.python_code || 'def extract(trace):\n    return True');
                }}
                className={selectedExtId === e.id ? 'bg-surface-container-highest border-primary-fixed' : 'bg-surface-container-lowest border-outline-variant hover:border-primary-fixed'}
              >
                <div>
                  <span 
                    className="font-bold text-on-surface mr-2 hover:underline"
                    onClick={(evt) => {
                      evt.stopPropagation();
                      setSelectedExtId(e.id);
                      setExtName(e.name);
                      setExtReturnType(e.return_type);
                      setExtPythonCode(e.python_code || 'def extract(trace):\n    return True');
                    }}
                  >
                    {e.id} ({e.name})
                  </span>
                  <Text variant="mono" as="span" className="uppercase text-xs font-semibold">{e.return_type}</Text>
                </div>
                <Button 
                  variant="destructive"
                  size="sm"
                  onClick={(evt) => handleDeleteExtractor(e.id, evt)}
                >
                  Delete
                </Button>
              </BorderedSection>
            ))}
          </div>
        ) : (
          <Text variant="muted" className="italic">No extractors found.</Text>
        )}
      </BorderedSection>
    </div>
  );
}
