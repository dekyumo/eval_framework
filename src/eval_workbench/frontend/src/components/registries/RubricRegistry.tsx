import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { Select } from '../ui/Select';
import { TextAreaWithLabel } from '../ui/Textarea';
import { Heading, Text, FormLabel } from '../ui/Typography';
import { BorderedSection } from '../ui/PageLayout';

interface RubricItem {
  name: string;
  type: string;
  description?: string;
  prompt?: string;
}

interface Rubric {
  id: string;
  name: string;
  instructions: string;
  default_judge_prompt?: string;
  items: RubricItem[];
}

interface RubricRegistryProps {
  rubrics: Rubric[];
  onFetchAll: () => void;
}

export function RubricRegistry({ rubrics, onFetchAll }: RubricRegistryProps) {
  const [rubricName, setRubricName] = useState('');
  const [rubricInstructions, setRubricInstructions] = useState('');
  const [rubricDefaultJudgePrompt, setRubricDefaultJudgePrompt] = useState('Please evaluate the trace based on the following instructions: {instructions}');
  const [rubricFields, setRubricFields] = useState<any[]>([]);
  const [selectedRubricId, setSelectedRubricId] = useState<string | null>(null);

  const handleSaveRubric = async () => {
    if (!rubricName) return;
    try {
      const payload = {
        id: selectedRubricId || `rubric_${crypto.randomUUID().substring(0, 8)}`,
        name: rubricName,
        instructions: rubricInstructions,
        items: rubricFields.map(f => ({
          name: f.name || 'unnamed_field',
          type: f.type,
          description: f.description || ''
        })),
        default_judge_prompt: rubricDefaultJudgePrompt,
        fingerprint: 'local_edit',
        version: 1,
        frozen: false
      };
      await fetch('/api/registries/rubrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      setRubricName('');
      setRubricInstructions('');
      setRubricFields([]);
      setSelectedRubricId(null);
      onFetchAll();
    } catch(e) { console.error(e); }
  };

  const handleDeleteRubric = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await fetch(`/api/registries/rubrics/${id}`, { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error || "Failed to delete rubric");
        return;
      }
      onFetchAll();
    } catch(e) { console.error(e); }
  };

  return (
    <div className="space-y-6 text-on-surface">
      <Heading level={2} className="mb-4">Rubrics</Heading>
      <div>
        <FormLabel htmlFor="rubric_name">Rubric Name</FormLabel>
        <input 
          id="rubric_name" 
          value={rubricName}
          onChange={e => setRubricName(e.target.value)}
          className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed text-sm" 
          placeholder="e.g. Tone Polite" 
        />
      </div>
      <TextAreaWithLabel
        id="rubric_instructions"
        label="Instructions"
        value={rubricInstructions}
        onChange={e => setRubricInstructions(e.target.value)}
        className="h-32"
        placeholder="Instructions for the human or AI grader..." 
      />
      <TextAreaWithLabel
        id="rubric_prompt"
        label="Judge Prompt (LLM)"
        value={rubricDefaultJudgePrompt}
        onChange={e => setRubricDefaultJudgePrompt(e.target.value)}
        className="h-20"
      />
      <div className="bg-surface-container-low border border-outline-variant rounded-lg p-4 space-y-4">
        <Heading level={3}>Fields</Heading>
        {rubricFields.map((field, idx) => (
          <div key={idx} className="grid grid-cols-[1fr,150px,1fr,40px] gap-4 items-end mb-4 bg-surface-container p-3 rounded-md border border-outline-variant">
            <div>
              <FormLabel htmlFor={`rubric_field_name_${idx}`}>Field Name</FormLabel>
              <input 
                id={`rubric_field_name_${idx}`}
                value={field.name}
                onChange={e => {
                  const newFields = [...rubricFields];
                  newFields[idx].name = e.target.value;
                  setRubricFields(newFields);
                }}
                className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface focus:outline-none focus:border-primary-fixed text-sm" 
                placeholder="e.g. is_polite" 
              />
            </div>
            <div>
              <FormLabel htmlFor={`rubric_field_type_${idx}`}>Type</FormLabel>
              <Select 
                id={`rubric_field_type_${idx}`}
                value={field.type}
                onChange={e => {
                  const newFields = [...rubricFields];
                  newFields[idx].type = e.target.value;
                  setRubricFields(newFields);
                }}
              >
                <option value="bool">bool</option>
                <option value="int">int</option>
                <option value="float">float</option>
                <option value="enum">enum</option>
              </Select>
            </div>
            <div>
              <FormLabel htmlFor={`rubric_field_desc_${idx}`}>Description</FormLabel>
              <input 
                id={`rubric_field_desc_${idx}`}
                value={field.description}
                onChange={e => {
                  const newFields = [...rubricFields];
                  newFields[idx].description = e.target.value;
                  setRubricFields(newFields);
                }}
                className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface focus:outline-none focus:border-primary-fixed text-sm" 
                placeholder="Field description" 
              />
            </div>
            <Button 
              variant="destructive"
              size="sm"
              className="h-10 px-2 font-bold"
              onClick={() => {
                setRubricFields(rubricFields.filter((_, i) => i !== idx));
              }}
            >
              ×
            </Button>
          </div>
        ))}
        <Button 
          variant="normal"
          size="sm"
          onClick={() => setRubricFields([...rubricFields, { name: '', type: 'bool', description: '' }])}
        >
          + Add Field
        </Button>
      </div>
      <div className="flex justify-end gap-3 mt-4">
        {selectedRubricId && (
          <Button 
            variant="normal"
            className="mr-auto"
            onClick={() => {
              setSelectedRubricId(null);
              setRubricName('');
              setRubricInstructions('');
              setRubricFields([]);
            }}
          >
            Cancel Edit
          </Button>
        )}
        <Button 
          variant="cta"
          onClick={handleSaveRubric}
        >
          {selectedRubricId ? 'Update Rubric' : 'Save Rubric'}
        </Button>
      </div>
      
      <BorderedSection position="top" className="space-y-4">
        <Heading level={3}>Existing Rubrics</Heading>
        {rubrics.length > 0 ? (
          <div className="space-y-2">
            {rubrics.map((e: any) => (
              <BorderedSection 
                key={e.id} 
                data-testid={`rubric-item-${e.name}`}
                onClick={() => {
                  setSelectedRubricId(e.id);
                  setRubricName(e.name);
                  setRubricInstructions(e.instructions || '');
                  setRubricDefaultJudgePrompt(e.default_judge_prompt || 'Please evaluate the trace based on the following instructions: {instructions}');
                  setRubricFields((e.items || []).map((item: RubricItem) => ({
                    name: item.name,
                    type: item.type,
                    description: item.description || item.prompt || '',
                  })));
                }}
                className={selectedRubricId === e.id ? 'bg-surface-container-highest border-primary-fixed' : 'bg-surface-container-lowest border-outline-variant hover:border-primary-fixed'}
              >
                <span 
                  className="font-bold text-on-surface hover:underline"
                  onClick={(evt) => {
                    evt.stopPropagation();
                    setSelectedRubricId(e.id);
                    setRubricName(e.name);
                    setRubricInstructions(e.instructions || '');
                    setRubricDefaultJudgePrompt(e.default_judge_prompt || 'Please evaluate the trace based on the following instructions: {instructions}');
                    setRubricFields((e.items || []).map((item: RubricItem) => ({
                    name: item.name,
                    type: item.type,
                    description: item.description || item.prompt || '',
                  })));
                  }}
                >
                  {e.name}
                </span>
                <Button 
                  variant="destructive"
                  size="sm"
                  onClick={(evt) => handleDeleteRubric(e.id, evt)}
                >
                  Delete
                </Button>
              </BorderedSection>
            ))}
          </div>
        ) : (
          <Text variant="muted" className="italic">No rubrics found.</Text>
        )}
      </BorderedSection>
    </div>
  );
}
