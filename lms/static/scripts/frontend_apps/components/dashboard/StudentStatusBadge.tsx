import classnames from 'classnames';

/**
 * Grade syncing:
 *  - `new`: A new grade exists that has not been synced.
 *  - `error`: Last attempt on syncing a grade failed.
 *  - `syncing`: Syncing grades is in progress for a particular student.
 * Assignment participation:
 *  - `drop`: The student dropped the assignment.
 */
export type StudentStatusType = 'new' | 'error' | 'syncing' | 'drop';

/**
 * Badge displaying different student-related statuses around assignment
 * participation or grade syncing
 */
export default function StudentStatusBadge({
  type,
}: {
  type: StudentStatusType;
}) {
  return (
    <div
      className={classnames(
        'px-1 py-0.5 rounded cursor-auto font-bold uppercase text-[0.65rem]',
        {
          'bg-grey-7 text-white': type === 'new' || type === 'drop',
          'bg-grade-error-light text-grade-error': type === 'error',
          'bg-grey-2 text-grey-7': type === 'syncing',
        },
      )}
    >
      {type === 'new' && 'New'}
      {type === 'error' && 'Error'}
      {type === 'syncing' && 'Syncing'}
      {type === 'drop' && 'Drop'}
    </div>
  );
}
