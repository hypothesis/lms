import { createElement } from 'preact';
import propTypes from 'prop-types';
import { useEffect, useState } from 'preact/hooks';

import StudentSelector from './StudentSelector';
import updateClientConfig from '../utils/update-client-config';

/**
 * The LMSGrader component is fixed at the top of the page. This toolbar shows which assignment is currently
 * active as well as a list of students to both view and submit grades for.
 */

export default function LMSGrader({
  children,
  students,
  onChangeSelectedUser,
}) {
  // No initial current student selected
  const [currentStudentIndex, setCurrentStudentIndex] = useState(-1);

  useEffect(() => {
    if (students[currentStudentIndex]) {
      updateClientConfig({
        focus: {
          user: {
            username: students[currentStudentIndex].userid,
            displayName: students[currentStudentIndex].displayName,
          },
        },
      });
      // let the parent component know the index changed
      onChangeSelectedUser(students[currentStudentIndex].userid);
    }
  }, [students, currentStudentIndex, onChangeSelectedUser]);

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
            <h2>Course Name</h2>
            <h3>Assignment Name</h3>
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
  // Callback to alert the parent component that a change has occurred and re-rendering may be needed.
  onChangeSelectedUser: propTypes.func.isRequired,
  // List of students to grade
  students: propTypes.array.isRequired,
};
