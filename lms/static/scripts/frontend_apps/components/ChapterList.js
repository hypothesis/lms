import Table from './Table';

/**
 * @typedef {import('../api-types').Chapter} Chapter
 */

/**
 * @typedef ChapterListProps
 * @prop {Chapter[]} chapters - List of available chapters
 * @prop {boolean} [isLoading] - Whether to show a loading indicator
 * @prop {Chapter|null} selectedChapter - The chapter within `chapters` which is currently selected
 * @prop {(c: Chapter) => void} onSelectChapter - Callback invoked when the user selects a chapter
 * @prop {(c: Chapter) => void} onUseChapter -
 *   Callback invoked when user confirms they want to use the selected chapter for
 *   an assignment.
 */

/**
 * Component that presents a list of chapters from a book and allows the user
 * to choose one for an assignment.
 *
 * @param {ChapterListProps} props
 */
export default function ChapterList({
  chapters,
  isLoading = false,
  selectedChapter,
  onSelectChapter,
  onUseChapter,
}) {
  const columns = [
    {
      label: 'Title',
    },
    {
      label: 'Page',
    },
  ];

  return (
    <Table
      accessibleLabel="Table of Contents"
      columns={columns}
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
