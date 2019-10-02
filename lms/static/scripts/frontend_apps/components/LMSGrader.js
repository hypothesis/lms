import { createElement } from 'preact';
import propTypes from 'prop-types';
import { useState } from 'preact/hooks';

import StudentSelector from './StudentSelector';
/**
 * The LMSGrader component is fixed at the top of the page. This toolbar shows which assignment is currently
 * active as well as a list of students to both view and submit grades for.
 */

export default function LMSGrader({ children, students }) {
  // No initial current student selected
  const [currentStudentIndex, setCurrentStudentIndex] = useState(-1);
  /**
   * Shows the current student index if a user is selected, or the
   * total student count otherwise.
   */
  const renderStudentCount = () => {
    if (currentStudentIndex >= 0) {
      return <span>{`${currentStudentIndex + 1}/${students.length}`}</span>;
    } else {
      return <span>{`${students.length} students`}</span>;
    }
  };

  /**
   * Callback to set the current selected student.
   */
  const onSelectStudent = studentIndex => {
    setCurrentStudentIndex(studentIndex);
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
          <li className="LMSGrader__student-picker">
            <StudentSelector
              onSelectStudent={onSelectStudent}
              students={students}
              selectedStudentIndex={currentStudentIndex}
            />
          </li>
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
