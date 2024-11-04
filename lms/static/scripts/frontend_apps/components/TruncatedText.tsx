import classnames from 'classnames';
import type { JSX } from 'preact';
import { useLayoutEffect, useRef, useState } from 'preact/hooks';

export type TruncatedTextProps = JSX.HTMLAttributes<HTMLSpanElement> & {
  children: string;
  className?: never;
  classes?: string | string[];
};

/**
 * A text container that elides its content.
 *
 * If the text overflows, the full content is added as a title for the
 * container.
 */
export default function TruncatedText({
  children,
  title,
  classes,
  ...htmlAttrs
}: TruncatedTextProps) {
  const [overflow, setOverflow] = useState(false);
  const ref = useRef<HTMLSpanElement | null>(null);

  useLayoutEffect(() => {
    const element = ref.current!;
    const computeIsOverflowing = () =>
      setOverflow(element.scrollWidth > element.clientWidth);

    // Check if element is overflowing on initial render
    computeIsOverflowing();
    // Re-check when the element is resized
    const observer = new ResizeObserver(computeIsOverflowing);
    observer.observe(element);

    return () => observer.disconnect();
  }, [children]);

  // An explicitly set `title` takes priority. Otherwise, use the content as
  // the title on overflow.
  const overflowTitle = title ?? (overflow ? children : undefined);

  return (
    <span
      ref={ref}
      className={classnames('truncate', classes)}
      title={overflowTitle}
      data-testid="truncated-text"
      {...htmlAttrs}
    >
      {children}
    </span>
  );
}
