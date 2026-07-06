interface ConfirmCardProps {
  title: string;
  description: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmCard({ title, description, onConfirm, onCancel }: ConfirmCardProps) {
  return (
    <div className="bg-surface-container rounded-lg border border-outline-variant shadow-sm p-5 max-w-sm text-on-surface">
      <h3 className="font-bold text-slate-800 text-lg mb-2">{title}</h3>
      <p className="text-slate-600 text-sm mb-5">{description}</p>
      <div className="flex gap-3 justify-end">
        <button 
          onClick={onCancel}
          className="px-4 py-2 rounded-md font-medium text-slate-600 hover:bg-slate-100 transition-colors"
        >
          Cancel
        </button>
        <button 
          onClick={onConfirm}
          className="px-4 py-2 rounded-md font-medium bg-orange-600 text-white hover:bg-orange-700 transition-colors"
        >
          Confirm
        </button>
      </div>
    </div>
  );
}
