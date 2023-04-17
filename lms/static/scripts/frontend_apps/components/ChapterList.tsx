import { DataTable, Scroll } from '@hypothesis/frontend-shared/lib/next';
import { useEffect, useRef } from 'preact/hooks';

import type { Chapter } from '../api-types';

export type ChapterListProps = {
  /** List of available chapters */
  chapters: Chapter[];
  isLoading?: boolean;
  /** The Chapter within chapters which is currently selected */
  selectedChapter: Chapter | null;
  /** Callback invoked when a user selects a chapter */
  onSelectChapter: (c: Chapter) => void;

  /**
   * Callback invoked when user confirms the selected chapter for an assignment
   */
  onUseChapter: (c: Chapter) => void;
};

/**
 * Component that presents a list of chapters from a book and allows the user
 * to choose one for an assignment.
 */
export default function ChapterList({
  chapters,
  isLoading = false,
  selectedChapter,
  onSelectChapter,
  onUseChapter,
}: ChapterListProps) {
  const tableRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    // Focus the data-table widget when the component is first rendered
    tableRef.current!.focus();
    // We only want to run this effect once.
    //
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const columns = [
    {
      label: 'Title',
      field: 'title',
    },
    {
      label: 'Location',
      field: 'page',
      classes: 'w-32',
    },
  ];

  return (
    <Scroll>
      <DataTable
        elementRef={tableRef}
        title="Table of Contents"
        columns={columns}
        loading={isLoading}
        rows={chapters}
        onSelectRow={onSelectChapter}
        onConfirmRow={onUseChapter}
        selectedRow={selectedChapter}
        data-testid="chapter-table"
        tabIndex={-1}
      />
    </Scroll>
  );
}
