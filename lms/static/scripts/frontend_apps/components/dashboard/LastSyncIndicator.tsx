import type { IconComponent } from '@hypothesis/frontend-shared';
import { formatDateTime } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useMemo } from 'preact/hooks';

import type { ISODateTime } from '../../api-types';
import RelativeTime from '../RelativeTime';

export type LastSyncIndicatorProps = {
  icon: IconComponent;
  taskName: string;
  dateTime: ISODateTime | null;
};

/**
 * Represents the last time a task that syncs periodically happened
 */
export default function LastSyncIndicator({
  icon: Icon,
  taskName,
  dateTime,
}: LastSyncIndicatorProps) {
  const absoluteDate = useMemo(
    () =>
      dateTime ? formatDateTime(dateTime, { includeWeekday: true }) : undefined,
    [dateTime],
  );

  return (
    <div
      className={classnames(
        'flex gap-x-1 items-center p-1.5',
        'bg-grey-2 text-color-text-light cursor-default',
        'first:rounded-l last:rounded-r',
      )}
      title={absoluteDate && `${taskName} last synced on ${absoluteDate}`}
      data-testid="container"
    >
      <Icon />
      <span className="font-bold">{taskName}:</span>
      {dateTime ? (
        <RelativeTime dateTime={dateTime} withTitle={false} />
      ) : (
        <span data-testid="syncing">syncing…</span>
      )}
    </div>
  );
}
