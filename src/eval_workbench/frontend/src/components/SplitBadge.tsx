import { cn } from '../utils/cn';

export function SplitBadge({ split }: { split: "optimisation" | "judging" | "train" | "test" }) {
  const isTrain = split === "optimisation" || split === "train";
  const label = split === "optimisation" ? "train" : (split === "judging" ? "test" : split);
  
  return (
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider",
      isTrain ? "bg-teal-100 text-teal-800" : "bg-violet-100 text-violet-800"
    )}>
      {label}
    </span>
  );
}
