import * as React from 'react';
import { cn } from '../../utils/cn';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  fullWidth?: boolean;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, fullWidth = true, children, ...props }, ref) => {
    return (
      <select
        ref={ref}
        className={cn(
          "bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface focus:outline-none focus:border-primary-fixed text-sm transition-colors disabled:opacity-50",
          fullWidth ? "w-full" : "w-auto",
          className
        )}
        {...props}
      >
        {children}
      </select>
    );
  }
);
Select.displayName = 'Select';

export { Select };
