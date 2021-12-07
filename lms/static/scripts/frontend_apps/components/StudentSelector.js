import { Icon, IconButton } from '@hypothesis/frontend-shared';
import classNames from 'classnames';

/**
 * @typedef Student
 * @prop {string} displayName
 */

/**
 * @typedef StudentSelectorProps
 * @prop {(index: number) => any} onSelectStudent -
 *   Callback invoked when the selected student changes
 * @prop {number} selectedStudentIndex -
 *   Index of selected student in `students` or -1 if no student is selected
 * @prop {Student[]} students - Ordered list of students to display in the drop-down
 */

/**
 * A student navigation tool which shows a student selection list and a previous and next button.
 *
 * @param {StudentSelectorProps} props
 */
export default function StudentSelector({
  onSelectStudent,
  selectedStudentIndex,
  students,
}) {
  // Disable the next button if at the end of the list. The length is equal to
  // the student list plus the default "All Students" option.
  const hasNextView = selectedStudentIndex + 1 < students.length;
  // Disable the previous button only if the selectedStudentIndex is less than 0
  // indicating the "All Students" choice is selected.
  const hasPrevView = selectedStudentIndex >= 0;

  /**
   * Select the next student index in the list.
   */
  const onNextView = () => {
    onSelectStudent(selectedStudentIndex + 1);
  };
  /**
   * Select the previous student index in the list. The 0 index
   * represents "All Students."
   */
  const onPrevView = () => {
    onSelectStudent(selectedStudentIndex - 1);
  };

  /**
   * Build the <select> list from the current array of students.
   */
  const buildStudentList = () => {
    const options = students.map((student, i) => (
      <option
        key={`student-${i}`}
        selected={selectedStudentIndex === i}
        value={i}
      >
        {student.displayName}
      </option>
    ));
    options.unshift(
      <option
        key={'all-students'}
        selected={selectedStudentIndex === -1}
        value={-1}
      >
        All Students
      </option>
    );

    return (
      <span className="relative">
        {/*
        This lint issue may have arisen from browser inconsistency issues with
        `onChange` which have since been fixed. See browser compatibility note here:
        https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/change_event#annotations:xeC6ClQsEequhUdih2lXzw
        */}
        {/* eslint-disable-next-line jsx-a11y/no-onchange*/}
        <select
          className={classNames(
            'appearance-none w-full h-touch-minimum',
            'pl-4 pr-8', // Make room on right for custom down-caret Icon
            'xl:w-80', // Fix the width at wider viewports
            'hyp-u-outline-on-keyboard-focus--inset hyp-u-border',
            'border-r-0 border-l-0' // left and right borders off
          )}
          onChange={e => {
            onSelectStudent(
              parseInt(/** @type {HTMLInputElement} */ (e.target).value)
            );
          }}
        >
          {options}
        </select>
        <Icon
          classes="absolute top-0.5 right-3 pointer-events-none text-grey-4"
          name="caretDown"
        />{' '}
      </span>
    );
  };

  return (
    <div
      className={classNames(
        // Narrower widths: label above field
        'flex flex-col gap-1',
        // Wider widths: label to left of field
        'xl:flex-row xl:gap-3 xl:items-center'
      )}
    >
      <label
        className={classNames(
          'flex-grow font-medium text-sm leading-none',
          'xl:text-right'
        )}
        data-testid="student-selector-label"
      >
        {selectedStudentIndex >= 0 ? (
          <span>
            Student {`${selectedStudentIndex + 1} of ${students.length}`}
          </span>
        ) : (
          <span>{`${students.length} Students`}</span>
        )}
      </label>
      <div className="flex flex-row">
        <IconButton
          classes={classnames(
            'px-3',
            // IconButton styling sets a border radius. Turn it off on the
            // right for better alignment with the select element
            'rounded-r-none',
            'hyp-u-outline-on-keyboard-focus--inset'
          )}
          icon="arrowLeft"
          title="previous student"
          disabled={!hasPrevView}
          onClick={onPrevView}
          variant="dark"
        />
        <div className="w-full">{buildStudentList()}</div>
        <IconButton
          classes={classnames(
            'px-3',
            // Turn off border radius on left for better alignment with select
            'rounded-l-none',
            'hyp-u-outline-on-keyboard-focus--inset'
          )}
          icon="arrowRight"
          title="next student"
          disabled={!hasNextView}
          onClick={onNextView}
          variant="dark"
        />
      </div>
    </div>
  );
}
