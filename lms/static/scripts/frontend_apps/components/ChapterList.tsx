import {
  DataTable,
  Scroll,
  ScrollContainer,
} from '@hypothesis/frontend-shared';
import { useCallback, useEffect, useMemo, useRef } from 'preact/hooks';

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
 * Component that presents a book's table of contents and allows them to
 * select a range for an assignment.
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
    []
  );

  const renderItem = useCallback((chapter: Chapter, field: keyof Chapter) => {
    switch (field) {
      case 'page':
        return chapter.page;
      case 'title': {
        // DataTable doesn't have true support for hierarchical data structures.
        // Here we indicate the ToC level visually by indenting rows.
        const level = typeof chapter.level === 'number' ? chapter.level - 1 : 0;
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
  }, []);

  return (
    <ScrollContainer rounded>
      <Scroll>
        <DataTable
          elementRef={tableRef}
          title="Table of Contents"
          columns={columns}
          loading={isLoading}
          renderItem={renderItem}
          rows={chapters}
          onSelectRow={onSelectChapter}
          onConfirmRow={onUseChapter}
          selectedRow={selectedChapter}
          data-testid="chapter-table"
          tabIndex={-1}
          borderless
        />
      </Scroll>
    </ScrollContainer>
  );
}
