import { Popover } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { JSX } from 'preact';
import { useId, useLayoutEffect, useRef, useState } from 'preact/hooks';

export type TimeInputOption = {
  /** Text shown for — and inserted by — this suggestion. */
  label: string;
  /** Shown greyed out and not selectable. */
  disabled?: boolean;
};

/** Case- and whitespace-insensitive comparison key for labels and input. */
const normalize = (text: string) => text.toLowerCase().replace(/\s+/g, '');

export type TimeInputProps = {
  /**
   * Current text in the field. Free-form: it is not necessarily one of the
   * suggestions or even a valid time. The parent validates it.
   */
  value: string;

  /** Reports the text on every edit. Picking a suggestion reports its label. */
  onChange: (text: string) => void;

  /**
   * Invoked when editing finishes (blur, Enter, picking a suggestion) — the
   * parent's chance to normalize the text.
   */
  onCommit?: () => void;

  /**
   * Suggestions offered in the dropdown. They are filtered as the user types,
   * by label prefix ("3:3" offers "3:30 AM" and "3:30 PM").
   */
  options: TimeInputOption[];

  /** id for the input, letting an external `<label>` point at it. */
  inputId?: string;

  placeholder?: string;

  /** Classes for the input element. */
  classes?: string;
};

/**
 * A text field with time suggestions, mirroring the pickers in Canvas: the
 * user can either choose a suggestion or type a time by hand.
 *
 * The dropdown is rendered as page DOM (not a native `<select>` popup), so
 * its appearance does not depend on the browser or OS theme.
 */
export default function TimeInput({
  value,
  onChange,
  onCommit,
  options,
  inputId,
  placeholder,
  classes,
}: TimeInputProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const listboxRef = useRef<HTMLUListElement | null>(null);
  const listboxId = useId();
  const [open, setOpen] = useState(false);

  // Index into `filtered` of the option the arrow keys point at. The visual
  // highlight and `aria-activedescendant` follow it; focus stays on the input
  // so the user can keep typing.
  const [highlight, setHighlight] = useState(-1);

  const filterOptions = (text: string) =>
    options.filter(o => normalize(o.label).startsWith(normalize(text)));
  const filtered = filterOptions(value);

  // Keep the highlighted option in view while arrow keys move it beyond the
  // visible part of the list.
  useLayoutEffect(() => {
    if (highlight >= 0) {
      listboxRef.current
        ?.querySelector(`[data-index="${highlight}"]`)
        ?.scrollIntoView({ block: 'nearest' });
    }
  }, [highlight]);

  const close = () => {
    setOpen(false);
    setHighlight(-1);
  };

  const commit = () => {
    close();
    onCommit?.();
  };

  const openListbox = () => {
    if (open) {
      return;
    }
    setOpen(true);
    // Point the highlight at the current value, or the first selectable
    // suggestion when the text doesn't match one.
    const match = filtered.findIndex(
      o => !o.disabled && normalize(o.label) === normalize(value),
    );
    setHighlight(match >= 0 ? match : filtered.findIndex(o => !o.disabled));
  };

  const selectOption = (option: TimeInputOption) => {
    if (option.disabled) {
      return;
    }
    onChange(option.label);
    commit();
  };

  const onInput = (e: JSX.TargetedEvent<HTMLInputElement>) => {
    const text = e.currentTarget.value;
    setOpen(true);
    // Highlight the first selectable suggestion still matching the text.
    setHighlight(filterOptions(text).findIndex(o => !o.disabled));
    onChange(text);
  };

  const moveHighlight = (dir: 1 | -1) => {
    setHighlight(current => {
      let next = current;
      do {
        next += dir;
      } while (filtered[next]?.disabled);
      // Stop at either end of the list rather than wrapping around.
      return next >= 0 && next < filtered.length ? next : current;
    });
  };

  const onKeyDown = (e: JSX.TargetedKeyboardEvent<HTMLInputElement>) => {
    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowUp':
        e.preventDefault();
        if (!open) {
          openListbox();
        } else {
          moveHighlight(e.key === 'ArrowDown' ? 1 : -1);
        }
        break;
      case 'Enter': {
        // Typed as always-present, but `highlight` is -1 with no selection.
        const highlighted = filtered[highlight] as TimeInputOption | undefined;
        if (open && highlighted && !highlighted.disabled) {
          // Swallow the implicit form submission only while the key means
          // "choose the highlighted suggestion".
          e.preventDefault();
          onChange(highlighted.label);
        }
        commit();
        break;
      }
      case 'Escape':
        close();
        break;
    }
  };

  const onBlur = (e: JSX.TargetedFocusEvent<HTMLInputElement>) => {
    // Ignore focus moving into the dropdown itself (e.g. its scrollbar).
    const next = e.relatedTarget as Node | null;
    if (next && containerRef.current?.contains(next)) {
      return;
    }
    commit();
  };

  return (
    <div className="relative" ref={containerRef}>
      <input
        type="text"
        autocomplete="off"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={open}
        // Only reference the listbox while it exists: its contents are not
        // rendered while the dropdown is closed.
        aria-controls={open ? listboxId : undefined}
        aria-activedescendant={
          highlight >= 0 ? `${listboxId}-${highlight}` : undefined
        }
        id={inputId}
        data-testid="time-input"
        className={classnames('w-full', classes)}
        placeholder={placeholder}
        value={value}
        onInput={onInput}
        onClick={openListbox}
        onKeyDown={onKeyDown}
        onBlur={onBlur}
      />
      <Popover
        open={open}
        onClose={close}
        anchorElementRef={containerRef}
        classes="max-h-64 overflow-y-auto"
      >
        <ul
          role="listbox"
          id={listboxId}
          ref={listboxRef}
          // Keep focus (and the pending blur-commit) on the input while
          // clicking options.
          onMouseDown={e => e.preventDefault()}
        >
          {filtered.length === 0 && (
            // Mirrors the Canvas pickers: an inert row marking "no matches".
            <li
              role="option"
              aria-disabled="true"
              aria-selected={false}
              className="p-2 text-grey-6"
            >
              ---
            </li>
          )}
          {filtered.map((option, index) => (
            // Keyboard access goes through the combobox input (arrow keys +
            // Enter), per the ARIA combobox pattern; the rows themselves are
            // never focusable.
            // eslint-disable-next-line jsx-a11y/click-events-have-key-events
            <li
              key={option.label}
              id={`${listboxId}-${index}`}
              data-index={index}
              role="option"
              aria-disabled={option.disabled}
              aria-selected={normalize(option.label) === normalize(value)}
              className={classnames('px-2 py-1', {
                'bg-grey-2': index === highlight,
                'text-grey-6': option.disabled,
                'cursor-pointer': !option.disabled,
              })}
              onClick={() => selectOption(option)}
              onMouseMove={() => !option.disabled && setHighlight(index)}
            >
              {option.label}
            </li>
          ))}
        </ul>
      </Popover>
    </div>
  );
}
