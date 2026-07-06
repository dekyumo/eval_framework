import * as React from 'react';
import { cn } from '../../utils/cn';

export interface HeadingProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: 1 | 2 | 3 | 4;
}

export const Heading = React.forwardRef<HTMLHeadingElement, HeadingProps>(
  ({ className, level = 2, children, ...props }, ref) => {
    const Tag = `h${level}` as const;
    return (
      <Tag
        ref={ref as any}
        className={cn(
          "font-headline text-on-surface font-bold tracking-tight",
          level === 1 && "text-3xl",
          level === 2 && "text-2xl",
          level === 3 && "text-lg",
          level === 4 && "text-sm tracking-wider uppercase text-on-surface-variant font-mono",
          className
        )}
        {...props}
      >
        {children}
      </Tag>
    );
  }
);
Heading.displayName = 'Heading';

export interface TextProps extends React.HTMLAttributes<HTMLElement> {
  variant?: 'body' | 'muted' | 'mono' | 'caption';
  as?: 'p' | 'span' | 'div' | 'label';
}

export const Text = React.forwardRef<HTMLElement, TextProps>(
  ({ className, variant = 'body', as: Tag = 'p', children, ...props }, ref) => {
    return (
      <Tag
        ref={ref as any}
        className={cn(
          variant === 'body' && "text-on-surface text-sm leading-relaxed",
          variant === 'muted' && "text-on-surface-variant text-sm leading-relaxed",
          variant === 'caption' && "text-on-surface-variant text-xs",
          variant === 'mono' && "font-mono text-xs text-on-surface-variant bg-surface-container-high px-1.5 py-0.5 rounded",
          className
        )}
        {...props}
      >
        {children}
      </Tag>
    );
  }
);
Text.displayName = 'Text';

export interface FormLabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  className?: string;
}

export const FormLabel = React.forwardRef<HTMLLabelElement, FormLabelProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <label
        ref={ref}
        className={cn(
          "block text-sm font-semibold text-on-surface-variant mb-1 select-none",
          className
        )}
        {...props}
      >
        {children}
      </label>
    );
  }
);
FormLabel.displayName = 'FormLabel';
