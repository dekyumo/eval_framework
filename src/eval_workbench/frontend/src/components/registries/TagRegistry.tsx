import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { Heading, Text, FormLabel } from '../ui/Typography';
import { BorderedSection } from '../ui/PageLayout';

interface Tag {
  id: string;
  name: string;
  color: string;
  description: string;
}

interface TagRegistryProps {
  tags: Tag[];
  onFetchAll: () => void;
}

export function TagRegistry({ tags, onFetchAll }: TagRegistryProps) {
  const [tagName, setTagName] = useState('');
  const [tagColor, setTagColor] = useState('#31C48D');
  const [editingTag, setEditingTag] = useState<string | null>(null);

  const handleSaveTag = async () => {
    if (!tagName) return;
    try {
      const payload = {
        id: editingTag || tagName.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-'),
        name: tagName.trim(),
        color: tagColor,
        description: ''
      };
      const res = await fetch('/api/registries/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error || "Failed to save tag");
        return;
      }
      setTagName('');
      setEditingTag(null);
      onFetchAll();
    } catch(e) { console.error(e); }
  };

  const handleDeleteTag = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await fetch(`/api/registries/tags/${id}`, { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error || "Failed to delete tag");
        return;
      }
      onFetchAll();
    } catch(e) { console.error(e); }
  };

  return (
    <div className="space-y-6 text-on-surface">
      <Heading level={2} className="mb-4">Tags</Heading>
      <div className="flex gap-4">
        <div className="flex-1">
          <FormLabel htmlFor="tag_name">Tag Name</FormLabel>
          <input 
            id="tag_name" 
            value={tagName}
            onChange={e => setTagName(e.target.value)}
            className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed text-sm" 
            placeholder="e.g. pii-leak" 
          />
        </div>
        <div className="w-24">
          <FormLabel htmlFor="tag_color">Color</FormLabel>
          <input 
            id="tag_color" 
            type="color"
            value={tagColor}
            onChange={e => setTagColor(e.target.value)}
            className="w-full h-[42px] bg-surface-container-highest border border-outline-variant rounded-md p-1 cursor-pointer focus:outline-none focus:border-primary-fixed" 
          />
        </div>
      </div>
      <div className="flex justify-end gap-3 mt-4">
        {editingTag && (
          <Button 
            variant="normal"
            className="mr-auto"
            onClick={() => {
              setEditingTag(null);
              setTagName('');
            }}
          >
            Cancel Edit
          </Button>
        )}
        <Button 
          variant="cta"
          onClick={handleSaveTag}
        >
          {editingTag ? 'Update Tag' : 'Save Tag'}
        </Button>
      </div>
      
      <BorderedSection position="top" className="space-y-4">
        <Heading level={3}>Existing Tags</Heading>
        {tags.length > 0 ? (
          <div className="space-y-2">
            {tags.map((e: any, i: number) => (
              <BorderedSection 
                key={i} 
                data-testid={`tag-pill-${e.name}`}
                onClick={() => {
                  setEditingTag(e.id);
                  setTagName(e.name);
                  setTagColor(e.color);
                }}
              >
                <div className="flex items-center gap-3">
                  <span 
                    className="px-3 py-1 rounded-full text-xs font-semibold border font-mono select-none"
                    style={{ backgroundColor: `${e.color}20`, color: e.color, borderColor: e.color }}
                  >
                    {e.name}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <Button 
                    variant="ghost"
                    size="sm"
                    onClick={(evt) => {
                      evt.stopPropagation();
                      setEditingTag(e.id);
                      setTagName(e.name);
                      setTagColor(e.color);
                    }}
                    className="text-primary-fixed hover:text-white"
                  >
                    Edit
                  </Button>
                  <Button 
                    variant="destructive"
                    size="sm"
                    onClick={(evt) => handleDeleteTag(e.id, evt)}
                  >
                    Delete
                  </Button>
                </div>
              </BorderedSection>
            ))}
          </div>
        ) : (
          <Text variant="muted" className="italic">No tags found.</Text>
        )}
      </BorderedSection>
    </div>
  );
}
