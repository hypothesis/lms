import { DataTable, Scroll } from '@hypothesis/frontend-shared/lib/next';

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
        title="Table of Contents"
        columns={columns}
        loading={isLoading}
        rows={chapters}
        onSelectRow={onSelectChapter}
        onConfirmRow={onUseChapter}
        selectedRow={selectedChapter}
      />
    </Scroll>
  );
}
