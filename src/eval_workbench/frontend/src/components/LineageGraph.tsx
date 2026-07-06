import { Heading } from './ui/Typography';

export function LineageGraph({ manifest }: { manifest: any }) {
  if (!manifest) return null;

  return (
    <div className="bg-surface-container rounded-xl border border-outline-variant p-6">
      <Heading level={3} className="mb-4">Agent Topology</Heading>
      <div className="flex flex-wrap gap-4">
        {manifest.agents?.map((a: any) => (
          <div
            key={a.name}
            className="bg-surface-container-highest p-4 rounded-lg border border-outline-variant min-w-[200px]"
          >
            <div className="font-headline font-bold text-primary-fixed">{a.name}</div>
            <div className="text-xs text-on-surface-variant mb-2 font-mono">
              Model: {a.model_id}
            </div>

            {a.tool_ids?.length > 0 && (
              <div className="mt-3">
                <div className="text-xs font-semibold text-on-surface-variant mb-1 uppercase tracking-wider">
                  Tools
                </div>
                <div className="flex flex-wrap gap-1">
                  {a.tool_ids.map((tid: string) => (
                    <span
                      key={tid}
                      className="px-1.5 py-0.5 bg-surface-container border border-outline-variant rounded text-xs text-on-surface-variant font-mono"
                    >
                      {tid}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
