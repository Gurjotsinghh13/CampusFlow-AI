"use client";

import { cn } from "@/lib/utils";

interface MultiSelectOption {
  value: string;
  label: string;
  hint?: string;
}

interface MultiSelectChecklistProps {
  options: MultiSelectOption[];
  selected: string[];
  onChange: (values: string[]) => void;
  emptyText?: string;
  className?: string;
}

export function MultiSelectChecklist({
  options,
  selected,
  onChange,
  emptyText = "No options available",
  className,
}: MultiSelectChecklistProps) {
  function toggle(value: string) {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  }

  return (
    <div
      className={cn(
        "flex max-h-48 flex-col gap-0.5 overflow-y-auto scrollbar-thin rounded-md border border-input bg-card p-2",
        className
      )}
    >
      {options.length === 0 ? (
        <p className="px-2 py-3 text-center text-sm text-muted-foreground">{emptyText}</p>
      ) : (
        options.map((option) => (
          <label
            key={option.value}
            className="flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
          >
            <input
              type="checkbox"
              className="h-3.5 w-3.5 rounded border-input accent-primary"
              checked={selected.includes(option.value)}
              onChange={() => toggle(option.value)}
            />
            <span className="flex-1">{option.label}</span>
            {option.hint && <span className="text-xs text-muted-foreground">{option.hint}</span>}
          </label>
        ))
      )}
    </div>
  );
}
