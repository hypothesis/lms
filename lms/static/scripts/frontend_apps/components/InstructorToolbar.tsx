import { Link } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { Link as RouterLink } from 'wouter-preact';
import { useId, useRef, useState } from 'preact/hooks';

import { useConfig } from '../config';
import GradingControls from './GradingControls';

/**
 * Toolbar for instructors.
 * Shows assignment information and grading controls (for gradable assignments).
 */
export default function InstructorToolbar() {
  const { instructorToolbar, api } = useConfig();
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
    scoreMaximum,
    acceptGradingComments,
  } = instructorToolbar;

  const form = useRef<HTMLFormElement | null>(null);
  const withGradingControls = gradingEnabled && !!students;

  const submit = (event: Event) => {
    console.log(api);
    console.log(event);
  };



  return (
    <header
      className={classnames(
        'p-2',
        // Default and narrower screens: content is stacked vertically
        'grid grid-cols-1 items-center gap-x-4 gap-y-2',
        // Wider screens: assignment metadata and grading controls side by side
        'md:grid-cols-[1fr_auto] md:py-1',
      )}
    >
      <div className="space-y-1">
        <div
          className={classnames(
            // lays out assignment name and edit button
            'flex gap-x-2 items-center',
          )}
        >
          <h1
            className="text-lg font-semibold leading-none"
            data-testid="assignment-name"
          >
            {assignmentName}
          </h1>
          {editingEnabled && (
            <RouterLink href="/app/content-item-selection" asChild>
              <Link
                classes="text-xs"
                data-testid="edit"
                title="Edit assignment settings"
                underline="always"
              >
                Edit
              </Link>
            </RouterLink>
          )}
        <form
          action="/analytics/lti/assignment"
          ref={form}
          className="flex flex-row items-center space-x-2"
          onSubmit={submit}
          method="POST"
        >
 
          <input name="authorization" type="hidden" value={api.authToken}/>
          <button>ANALYTICS</button>
          </form>
        </div>
        <h2
          className="text-sm font-normal text-color-text-light leading-none"
          data-testid="course-name"
        >
          {courseName}
        </h2>
      </div>

      {withGradingControls ? (
        <GradingControls
          students={students}
          scoreMaximum={scoreMaximum ?? undefined}
          acceptComments={acceptGradingComments}
        />
      ) : (
        <div />
      )}
    </header>
  );
}
