import * as React from 'react';
import { cn } from '../../utils/cn';

interface PageContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'full' | 'standard' | 'contained' | 'centered';
}

export const PageContainer = React.forwardRef<HTMLDivElement, PageContainerProps>(
  ({ className, variant = 'standard', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "text-on-surface",
          variant === 'full' && "w-full h-full flex gap-6",
          variant === 'standard' && "w-full space-y-6",
          variant === 'contained' && "max-w-5xl mx-auto space-y-6",
          variant === 'centered' && "w-full max-w-3xl mx-auto flex flex-col gap-8",
          className
        )}
        {...props}
      />
    );
  }
);
PageContainer.displayName = 'PageContainer';

interface PageHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export const PageHeader = React.forwardRef<HTMLDivElement, PageHeaderProps>(
  ({ className, title, description, actions, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("flex justify-between items-end mb-6", className)}
        {...props}
      >
        <div>
          <h1 className="font-headline text-2xl font-bold tracking-tight text-on-surface">{title}</h1>
          {description && (
            <p className="font-body text-sm text-on-surface-variant mt-1">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-3">{actions}</div>}
      </div>
    );
  }
);
PageHeader.displayName = 'PageHeader';

interface PagePaneProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'card' | 'sidebar' | 'content' | 'low';
  title?: string;
  headerActions?: React.ReactNode;
}

export const PagePane = React.forwardRef<HTMLDivElement, PagePaneProps>(
  ({ className, variant = 'card', title, headerActions, children, ...props }, ref) => {
    if (variant === 'sidebar') {
      return (
        <div
          ref={ref}
          className={cn(
            "w-1/3 bg-surface-container rounded-xl border border-outline-variant overflow-hidden flex flex-col",
            className
          )}
          {...props}
        >
          {title && (
            <div className="p-4 border-b border-outline-variant bg-surface-container-low flex justify-between items-center shrink-0">
              <h2 className="text-lg font-bold font-headline text-on-surface">{title}</h2>
              {headerActions}
            </div>
          )}
          {children}
        </div>
      );
    }

    return (
      <div
        ref={ref}
        className={cn(
          "bg-surface-container rounded-xl border border-outline-variant",
          variant === 'card' && "p-6",
          variant === 'content' && "flex-1 p-6 overflow-y-auto",
          variant === 'low' && "p-4 bg-surface-container-low border border-outline-variant rounded-lg",
          className
        )}
        {...props}
      >
        {(title || headerActions) && (
          <div className="flex justify-between items-center mb-6">
            {title && <h2 className="text-2xl font-bold font-headline text-on-surface">{title}</h2>}
            {headerActions && <div className="flex items-center gap-2">{headerActions}</div>}
          </div>
        )}
        {children}
      </div>
    );
  }
);
PagePane.displayName = 'PagePane';

export interface BorderedSectionProps extends React.HTMLAttributes<HTMLDivElement> {
  position?: 'top' | 'bottom' | 'header' | 'footer' | 'item';
  children?: React.ReactNode;
}

export const BorderedSection = React.forwardRef<HTMLDivElement, BorderedSectionProps>(
  ({ className, position = 'item', children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          position === 'header' && "p-4 border-b border-outline-variant bg-surface-container-low flex justify-between items-center shrink-0",
          position === 'footer' && "mt-8 pt-4 border-t border-outline-variant flex gap-3 justify-end",
          position === 'top' && "pt-6 border-t border-outline-variant",
          position === 'bottom' && "pb-6 border-b border-outline-variant",
          position === 'item' && "p-3 bg-surface-container-lowest border border-outline-variant rounded-md flex justify-between items-center hover:border-primary-fixed cursor-pointer transition-colors",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
BorderedSection.displayName = 'BorderedSection';
