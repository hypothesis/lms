import classnames from 'classnames';
import type { ComponentChildren } from 'preact';

import GradingControls from './GradingControls';

export type GradingToolbarProps = {
  /** Iframe element displaying assignment content. */
  children: ComponentChildren;
  courseName: string;
  assignmentName: string;
};

/**
 * Assignment toolbar for instructors. Shows assignment information and grading
 * controls (for gradeable assignments).
 */
export default function GradingToolbar({
  children,
  assignmentName,
  courseName,
}: GradingToolbarProps) {
  return (
    <>
      <header
        className={classnames(
          'grid grid-cols-1 items-center gap-y-2 p-2',
          'lg:grid-cols-3 lg:gap-x-4 lg:px-3'
        )}
      >
        <div className="space-y-1">
          <h1
            className="text-lg font-semibold leading-none"
            data-testid="assignment-name"
          >
            {assignmentName}
          </h1>
          <h2
            className="text-sm font-normal text-color-text-light leading-none"
            data-testid="course-name"
          >
            {courseName}
          </h2>
        </div>

        <div
          className={classnames(
            'flex flex-col gap-2',
            'sm:flex-row',
            'lg:col-span-2 lg:gap-4 ' /* cols 2-3 of 3 */
          )}
        >
          <GradingControls />
        </div>
      </header>
      {children}
    </>
  );
}
