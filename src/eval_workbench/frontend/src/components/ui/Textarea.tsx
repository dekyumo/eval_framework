import * as React from 'react';
import { cn } from '../../utils/cn';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  fullWidth?: boolean;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, fullWidth = true, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface focus:outline-none focus:border-primary-fixed text-sm transition-colors disabled:opacity-50 min-h-[80px]",
          fullWidth ? "w-full" : "w-auto",
          className
        )}
        {...props}
      />
    );
  }
);
Textarea.displayName = 'Textarea';

interface TextAreaWithLabelProps extends TextareaProps {
  label: string;
  id: string;
  containerClassName?: string;
}

const TextAreaWithLabel = React.forwardRef<HTMLTextAreaElement, TextAreaWithLabelProps>(
  ({ label, id, containerClassName, className, ...props }, ref) => {
    return (
      <div className={cn("flex flex-col gap-1 w-full", containerClassName)}>
        <label htmlFor={id} className="block text-sm font-semibold text-on-surface-variant mb-1">
          {label}
        </label>
        <Textarea id={id} ref={ref} className={className} {...props} />
      </div>
    );
  }
);
TextAreaWithLabel.displayName = 'TextAreaWithLabel';

export { Textarea, TextAreaWithLabel };
