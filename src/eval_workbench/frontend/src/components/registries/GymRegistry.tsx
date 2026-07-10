import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { TextAreaWithLabel } from '../ui/Textarea';
import { Heading, Text, FormLabel } from '../ui/Typography';
import { BorderedSection } from '../ui/PageLayout';

interface Gym {
  id: string;
  name: string;
  class_path: string;
  description: string;
}

interface GymRegistryProps {
  gyms: Gym[];
  onFetchAll: () => void;
}

export function GymRegistry({ gyms, onFetchAll }: GymRegistryProps) {
  const [gymName, setGymName] = useState('');
  const [gymClassPath, setGymClassPath] = useState('');
  const [gymDescription, setGymDescription] = useState('');
  const [selectedGymId, setSelectedGymId] = useState<string | null>(null);

  const resetForm = () => {
    setSelectedGymId(null);
    setGymName('');
    setGymClassPath('');
    setGymDescription('');
  };

  const handleSaveGym = async () => {
    if (!gymName || !gymClassPath) return;
    try {
      const payload = {
        ...(selectedGymId ? { id: selectedGymId } : {}),
        name: gymName.trim(),
        class_path: gymClassPath.trim(),
        description: gymDescription,
      };
      const res = await fetch('/api/registries/gyms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error || 'Failed to save gym');
        return;
      }
      resetForm();
      onFetchAll();
    } catch (e) { console.error(e); }
  };

  const handleDeleteGym = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await fetch(`/api/registries/gyms/${id}`, { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error || 'Failed to delete gym');
        return;
      }
      onFetchAll();
    } catch (e) { console.error(e); }
  };

  const loadGym = (g: Gym) => {
    setSelectedGymId(g.id);
    setGymName(g.name);
    setGymClassPath(g.class_path);
    setGymDescription(g.description || '');
  };

  return (
    <div className="space-y-6 text-on-surface">
      <Heading level={2} className="mb-4">Gyms</Heading>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <FormLabel htmlFor="gym_name">Name</FormLabel>
          <input
            id="gym_name"
            value={gymName}
            onChange={e => setGymName(e.target.value)}
            className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed text-sm"
            placeholder="e.g. Airline Gym"
          />
        </div>
        <div>
          <FormLabel htmlFor="gym_class_path">Class Path</FormLabel>
          <input
            id="gym_class_path"
            value={gymClassPath}
            onChange={e => setGymClassPath(e.target.value)}
            className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed text-sm font-mono"
            placeholder="e.g. my_pkg.envs.AirlineGym"
          />
        </div>
      </div>

      <TextAreaWithLabel
        id="gym_description"
        label="Description"
        value={gymDescription}
        onChange={e => setGymDescription(e.target.value)}
        className="text-sm h-28"
        placeholder="What this gym simulates and which methods it exposes as tools."
      />

      <div className="flex justify-end gap-3 mt-4">
        {selectedGymId && (
          <Button variant="normal" className="mr-auto" onClick={resetForm}>
            Cancel Edit
          </Button>
        )}
        <Button variant="cta" onClick={handleSaveGym}>
          {selectedGymId ? 'Update Gym' : 'Save Gym'}
        </Button>
      </div>

      <BorderedSection position="top" className="space-y-4">
        <Heading level={3}>Existing Gyms</Heading>
        {gyms.length > 0 ? (
          <div className="space-y-2">
            {gyms.map((g) => (
              <BorderedSection
                key={g.id}
                data-testid={`gym-item-${g.name}`}
                onClick={() => loadGym(g)}
                className={selectedGymId === g.id ? 'bg-surface-container-highest border-primary-fixed' : 'bg-surface-container-lowest border-outline-variant hover:border-primary-fixed'}
              >
                <div>
                  <span
                    className="font-bold text-on-surface mr-2 hover:underline"
                    onClick={(evt) => { evt.stopPropagation(); loadGym(g); }}
                  >
                    {g.id} ({g.name})
                  </span>
                  <Text variant="mono" as="span" className="text-xs">{g.class_path}</Text>
                </div>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={(evt) => handleDeleteGym(g.id, evt)}
                >
                  Delete
                </Button>
              </BorderedSection>
            ))}
          </div>
        ) : (
          <Text variant="muted" className="italic">No gyms found.</Text>
        )}
      </BorderedSection>
    </div>
  );
}
