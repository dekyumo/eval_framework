import { useState, useEffect } from 'react';
import { DatasetRegistry } from '../components/registries/DatasetRegistry';
import { TagRegistry } from '../components/registries/TagRegistry';
import { RubricRegistry } from '../components/registries/RubricRegistry';
import { ExtractorRegistry } from '../components/registries/ExtractorRegistry';
import { Button } from '../components/ui/Button';
import { PageContainer, PagePane, BorderedSection } from '../components/ui/PageLayout';

export function Registries() {
  const [activeTab, setActiveTab] = useState<'datasets' | 'tags' | 'rubrics' | 'extractors'>('extractors');
  const [extractors, setExtractors] = useState<any[]>([]);
  const [rubricsList, setRubricsList] = useState<any[]>([]);
  const [tagsList, setTagsList] = useState<any[]>([]);
  const [datasetsList, setDatasetsList] = useState<any[]>([]);

  const fetchAll = () => {
    fetch('/api/registries/extractors').then(res => res.json()).then(data => { if (Array.isArray(data)) setExtractors(data); }).catch(console.error);
    fetch('/api/registries/rubrics').then(res => res.json()).then(data => { if (Array.isArray(data)) setRubricsList(data); }).catch(console.error);
    fetch('/api/registries/tags').then(res => res.json()).then(data => { if (Array.isArray(data)) setTagsList(data); }).catch(console.error);
    fetch('/api/registries/datasets').then(res => res.json()).then(data => { if (Array.isArray(data)) setDatasetsList(data); }).catch(console.error);
  };

  useEffect(() => {
    fetchAll();
  }, []);

  return (
    <PageContainer variant="full" className="flex-col">
      <PagePane variant="sidebar" className="w-full h-full flex flex-col">
        <BorderedSection position="header" className="p-2 gap-2 justify-start">
          {['datasets', 'tags', 'rubrics', 'extractors'].map(tab => (
            <Button 
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              variant={activeTab === tab ? 'normal' : 'ghost'}
              className={activeTab === tab ? 'text-primary-fixed font-bold capitalize' : 'capitalize font-bold'}
            >
              {tab}
            </Button>
          ))}
        </BorderedSection>
        
        <div className="flex-1 p-6 overflow-y-auto">
          {activeTab === 'extractors' && (
            <ExtractorRegistry extractors={extractors} onFetchAll={fetchAll} />
          )}
          
          {activeTab === 'rubrics' && (
            <RubricRegistry rubrics={rubricsList} onFetchAll={fetchAll} />
          )}
          
          {activeTab === 'tags' && (
            <TagRegistry tags={tagsList} onFetchAll={fetchAll} />
          )}
          
          {activeTab === 'datasets' && (
            <DatasetRegistry datasets={datasetsList} onFetchAll={fetchAll} />
          )}
        </div>
      </PagePane>
    </PageContainer>
  );
}
