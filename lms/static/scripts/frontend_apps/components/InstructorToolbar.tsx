import { LinkButton } from '@hypothesis/frontend-shared/lib/next';
import classnames from 'classnames';

import GradingControls from './GradingControls';
import { useConfig } from '../config';

/**
 * Toolbar for instructors.
 * Shows assignment information and grading controls (for gradeable assignments).
 */
export default function InstructorToolbar() {
  const { instructorToolbar } = useConfig();
  if (!instructorToolbar) {
    // User is not an instructor or toolbar is disabled in the current environment.
    return null;
  }

  const {
    students,
    courseName,
    assignmentName,
    editingEnabled,
    gradingEnabled,
  } = instructorToolbar;

  return (
    <header
      className={classnames(
        'grid grid-cols-1 items-center gap-y-2 p-2',
        'lg:grid-cols-3 lg:gap-x-4 lg:px-3'
      )}
    >
      <div className="space-y-1">
        <div className="flex gap-x-2 items-center">
          <h1
            className="text-lg font-semibold leading-none"
            data-testid="assignment-name"
          >
            {assignmentName}
          </h1>
          {editingEnabled && (
            <LinkButton
              classes="text-xs"
              data-testid="edit"
              title="Edit assignment settings"
              underline="always"
            >
              Edit
            </LinkButton>
          )}
        </div>
        <h2
          className="text-sm font-normal text-color-text-light leading-none"
          data-testid="course-name"
        >
          {courseName}
        </h2>
      </div>

      <div
        className={classnames('lg:col-span-2 lg:gap-4 ' /* cols 2-3 of 3 */)}
      >
        {gradingEnabled && students && <GradingControls students={students} />}
      </div>
    </header>
  );
}
