'use client';

import { cn } from '@/lib/utils';
import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

export const Input = forwardRef<HTMLInputElement, InputProps>(({ className, ...props }, ref) => {
  return (
    <input
      ref={ref}
      className={cn(
        'flex h-10 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-white',
        'placeholder:text-text-secondary',
        'focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    />
  );
});

Input.displayName = 'Input';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, ...props }, ref) => {
  return (
    <textarea
      ref={ref}
      className={cn(
        'flex min-h-[80px] w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-white',
        'placeholder:text-text-secondary',
        'focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
        'disabled:cursor-not-allowed disabled:opacity-50',
        'resize-none',
        className
      )}
      {...props}
    />
  );
});

Textarea.displayName = 'Textarea';
