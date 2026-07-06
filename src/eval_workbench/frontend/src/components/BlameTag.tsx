import { cn } from '../utils/cn';

interface BlameTagProps {
  type: "caller" | "agent" | "framework";
}

export function BlameTag({ type }: BlameTagProps) {
  const styles = {
    caller: "bg-orange-100 text-orange-800 border-orange-200",
    agent: "bg-red-100 text-red-800 border-red-200",
    framework: "bg-purple-100 text-purple-800 border-purple-200"
  };

  return (
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-xs font-bold border uppercase tracking-wider", styles[type])}>
      {type} error
    </span>
  );
}
