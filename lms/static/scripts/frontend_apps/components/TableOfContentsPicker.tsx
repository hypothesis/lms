import {
  DataTable,
  Scroll,
  ScrollContainer,
} from '@hypothesis/frontend-shared';
import { useCallback, useEffect, useMemo, useRef } from 'preact/hooks';

import type { TableOfContentsEntry } from '../api-types';

export type TableOfContentsPickerProps = {
  /**
   * Table of contents as a flat list. The hierarchical structure is indicated
   * by the {@link TableOfContentsEntry.level} property.
   */
  entries: TableOfContentsEntry[];
  isLoading?: boolean;
  /** The entry within `entries` which is currently selected */
  selectedEntry: TableOfContentsEntry | null;
  /** Callback invoked when a user selects an entry */
  onSelectEntry: (c: TableOfContentsEntry) => void;

  /**
   * Callback invoked when user confirms the selected entry for an assignment
   */
  onConfirmEntry: (c: TableOfContentsEntry) => void;
};

/**
 * Component that presents a book's table of contents and allows user to select
 * a range for an assignment.
 */
export default function TableOfContentsPicker({
  entries,
  isLoading = false,
  selectedEntry,
  onSelectEntry,
  onConfirmEntry,
}: TableOfContentsPickerProps) {
  const tableRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    // Focus the data-table widget when the component is first rendered
    tableRef.current!.focus();
    // We only want to run this effect once.
    //
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const columns = useMemo(
    () => [
      {
        label: 'Title',
        field: 'title',
      },
      {
        label: 'Page',
        field: 'page',
        classes: 'w-32',
      },
    ],
    [],
  );

  const renderItem = useCallback(
    (chapter: TableOfContentsEntry, field: keyof TableOfContentsEntry) => {
      switch (field) {
        case 'page':
          return chapter.page;
        case 'title': {
          // DataTable doesn't have true support for hierarchical data structures.
          // Here we indicate the ToC level visually by indenting rows.
          const level =
            typeof chapter.level === 'number' ? chapter.level - 1 : 0;
          return (
            <>
              <span
                data-testid="toc-indent"
                data-level={level}
                style={{ display: 'inline-block', width: `${level * 20}px` }}
              />
              {chapter.title}
            </>
          );
        }
        /* istanbul ignore next */
        default:
          return '';
      }
    },
    [],
  );

  return (
    <ScrollContainer rounded>
      <Scroll>
        <DataTable
          elementRef={tableRef}
          title="Table of Contents"
          columns={columns}
          loading={isLoading}
          renderItem={renderItem}
          rows={entries}
          onSelectRow={onSelectEntry}
          onConfirmRow={onConfirmEntry}
          selectedRow={selectedEntry}
          data-testid="toc-table"
          tabIndex={-1}
          borderless
        />
      </Scroll>
    </ScrollContainer>
  );
}
