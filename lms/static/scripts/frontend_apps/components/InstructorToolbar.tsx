import { LinkButton } from '@hypothesis/frontend-shared/lib/next';
import classnames from 'classnames';

import { useConfig } from '../config';
import GradingControls from './GradingControls';

/** Create and submit a hidden form. */
function submitForm(
  method: 'GET' | 'POST',
  action: string,
  fields: Record<string, string>
) {
  const form = document.createElement('form');
  form.method = method;
  form.action = action;
  for (const [name, value] of Object.entries(fields)) {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    form.append(input);
  }
  document.body.append(form);
  form.submit();
}

/**
 * Toolbar for instructors.
 * Shows assignment information and grading controls (for gradeable assignments).
 */
export default function InstructorToolbar() {
  const { editing, instructorToolbar } = useConfig();

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

  const onEdit = async () => {
    if (!editing) {
      return;
    }
    submitForm('POST', editing.form_action, {
      ...editing.formFields,
      edit: 'true',
    });
  };

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
              onClick={onEdit}
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
