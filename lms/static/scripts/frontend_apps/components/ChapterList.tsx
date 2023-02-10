import { Table } from '@hypothesis/frontend-shared';

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
    },
    {
      label: 'Location',
      classes: 'w-32',
    },
  ];

  return (
    <Table
      accessibleLabel="Table of Contents"
      classes="ChapterList"
      tableHeaders={columns}
      isLoading={isLoading}
      items={chapters}
      onSelectItem={onSelectChapter}
      onUseItem={onUseChapter}
      selectedItem={selectedChapter}
      renderItem={chapter => (
        <>
          <td aria-label={chapter.title}>{chapter.title}</td>
          <td>{chapter.page}</td>
        </>
      )}
    />
  );
}
