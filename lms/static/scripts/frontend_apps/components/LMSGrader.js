import { createElement } from 'preact';
import propTypes from 'prop-types';

/**
 * The LMSGrader component is fixed at the top of the page. This toolbar shows which assignment is currently
 * active as well as a list of students to both view and submit grades for.
 */

export default function LMSGrader({ children, students }) {
  /**
   * Shows the current student index if a user is selected, or the
   * total student count otherwise.
   */
  const renderStudentCount = () => {
    return <span>{`${students.length} students`}</span>;
  };

  return (
    <div className="LMSGrader">
      <header>
        <ul className="LMSGrader__grading-components">
          <li className="LMSGrader__assignment">
            {
              // placeholder for course name and assignment
            }
          </li>
          <li className="LMSGrader__student-index">{renderStudentCount()}</li>
          <li className="LMSGrader__student-picker" />
        </ul>
      </header>
      {children}
    </div>
  );
}

LMSGrader.propTypes = {
  // iframe to pass along
  children: propTypes.node.isRequired,
  // List of students to grade
  students: propTypes.array.isRequired,
};
