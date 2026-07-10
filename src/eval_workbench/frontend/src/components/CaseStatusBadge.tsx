export type CaseStatusBadgeLabel = 'not-gen' | 'not-eval' | 'ran';
export type CaseStatusBadgeVariant = 'pass' | 'margin' | 'fail';

const VARIANT_STYLES: Record<CaseStatusBadgeVariant, string> = {
  pass: 'bg-semantic-pass/20 text-semantic-pass border-semantic-pass/30',
  margin: 'bg-semantic-margin/20 text-semantic-margin border-semantic-margin/30',
  fail: 'bg-semantic-fail/20 text-semantic-fail border-semantic-fail/30',
};

type CaseStatusBadgeProps = {
  label: CaseStatusBadgeLabel;
  variant: CaseStatusBadgeVariant;
};

export function CaseStatusBadge({ label, variant }: CaseStatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-1 py-px rounded text-[9px] font-bold font-mono border shrink-0 leading-none ${VARIANT_STYLES[variant]}`}
    >
      {label}
    </span>
  );
}
