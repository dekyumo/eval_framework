import * as React from 'react';
import { cn } from '../../utils/cn';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'normal' | 'cta' | 'destructive' | 'inactive' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'normal', size = 'default', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none disabled:opacity-50 disabled:pointer-events-none rounded-md select-none",
          // Variants
          variant === 'cta' && "bg-primary-container text-on-primary-container hover:bg-primary-fixed hover:text-white font-semibold shadow-sm",
          variant === 'normal' && "bg-surface-container-highest text-on-surface border border-outline-variant hover:bg-surface-variant hover:border-on-surface-variant",
          variant === 'destructive' && "text-semantic-fail hover:text-red-400 font-bold hover:bg-red-500/10",
          variant === 'inactive' && "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest",
          variant === 'outline' && "border border-outline-variant bg-transparent hover:bg-surface-container-highest text-on-surface",
          variant === 'ghost' && "hover:bg-surface-container-highest hover:text-on-surface text-on-surface-variant",
          // Sizes
          size === 'default' && "px-4 py-2 text-sm",
          size === 'sm' && "px-3 py-1 text-xs",
          size === 'lg' && "px-6 py-3 text-base",
          size === 'icon' && "p-2",
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button };
