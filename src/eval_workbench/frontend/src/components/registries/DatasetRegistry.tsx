import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { Heading, Text, FormLabel } from '../ui/Typography';
import { BorderedSection } from '../ui/PageLayout';

interface Dataset {
  id: string;
  name: string;
  case_ids: string[];
}

interface DatasetRegistryProps {
  datasets: Dataset[];
  onFetchAll: () => void;
}

export function DatasetRegistry({ datasets, onFetchAll }: DatasetRegistryProps) {
  const [datasetName, setDatasetName] = useState('');
  const [editingDatasetId, setEditingDatasetId] = useState<string | null>(null);

  const handleSaveDataset = async () => {
    if (!datasetName.trim()) return;
    
    // Check for duplicate name
    const isDuplicate = datasets.some(d => 
      d.name.toLowerCase() === datasetName.trim().toLowerCase() && d.id !== editingDatasetId
    );
    if (isDuplicate) {
      alert("A dataset with this name already exists. Dataset names must be unique.");
      return;
    }

    try {
      const payload = {
        id: editingDatasetId || `ds_${crypto.randomUUID().substring(0, 8)}`,
        name: datasetName.trim(),
        case_ids: editingDatasetId ? (datasets.find(d => d.id === editingDatasetId)?.case_ids || []) : []
      };
      await fetch('/api/registries/datasets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      setDatasetName('');
      setEditingDatasetId(null);
      onFetchAll();
    } catch(e) { console.error(e); }
  };

  const handleDeleteDataset = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await fetch(`/api/registries/datasets/${id}`, { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error || "Failed to delete dataset");
        return;
      }
      onFetchAll();
    } catch(e) { console.error(e); }
  };

  return (
    <div className="space-y-6 text-on-surface">
      <Heading level={2} className="mb-4">Datasets</Heading>
      <div>
        <FormLabel htmlFor="dataset_name">Dataset Name</FormLabel>
        <input 
          id="dataset_name" 
          value={datasetName}
          onChange={e => setDatasetName(e.target.value)}
          className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed text-sm" 
          placeholder="e.g. Flight Booking Golden Set" 
        />
      </div>
      <div className="flex justify-end gap-3 mt-4">
        {editingDatasetId && (
          <Button 
            variant="normal"
            className="mr-auto"
            onClick={() => {
              setEditingDatasetId(null);
              setDatasetName('');
            }}
          >
            Cancel
          </Button>
        )}
        <Button 
          variant="cta"
          onClick={handleSaveDataset}
        >
          {editingDatasetId ? 'Update Dataset' : 'Save Dataset'}
        </Button>
      </div>
      
      <BorderedSection position="top" className="space-y-4">
        <Heading level={3}>Existing Datasets</Heading>
        {datasets.length > 0 ? (
          <div className="space-y-2">
            {datasets.map((e: any, i: number) => (
              <BorderedSection 
                key={i} 
                data-testid={`dataset-item-${e.name}`}
                onClick={() => {
                  setDatasetName(e.name);
                  setEditingDatasetId(e.id);
                }}
              >
                <div>
                  <span 
                    className="font-bold text-on-surface mr-2 cursor-pointer hover:underline"
                    onClick={(evt) => {
                      evt.stopPropagation();
                      setDatasetName(e.name);
                      setEditingDatasetId(e.id);
                    }}
                  >
                    {e.name}
                  </span>
                  <Text variant="muted" as="span" className="text-xs">({(e.case_ids || []).length} cases)</Text>
                </div>
                <Button 
                  variant="destructive"
                  size="sm"
                  onClick={(event) => {
                    event.stopPropagation();
                    handleDeleteDataset(e.id, event);
                  }}
                >
                  Delete
                </Button>
              </BorderedSection>
            ))}
          </div>
        ) : (
          <Text variant="muted" className="italic">No datasets found.</Text>
        )}
      </BorderedSection>
    </div>
  );
}
