import { createElement } from 'preact';
import propTypes from 'prop-types';
import { useEffect, useState } from 'preact/hooks';

import StudentSelector from './StudentSelector';
import SubmitGradeForm from './SubmitGradeForm';
import {
  updateClientConfig,
  removeClientConfig,
} from '../utils/update-client-config';

/**
 * The LMSGrader component is fixed at the top of the page. This toolbar shows which assignment is currently
 * active as well as a list of students to both view and submit grades for.
 */

export default function LMSGrader({
  children,
  assignmentName,
  courseName,
  students,
  onChangeSelectedUser,
}) {
  // No initial current student selected
  const [currentStudentIndex, setCurrentStudentIndex] = useState(-1);

  useEffect(() => {
    if (students[currentStudentIndex]) {
      // set focused user
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
    } else {
      // clear focused user
      removeClientConfig(['focus']);
      onChangeSelectedUser('0'); // any non-real userid will work
    }
  }, [students, currentStudentIndex, onChangeSelectedUser]);

  /**
   * Shows the current student index if a user is selected, or the
   * total student count otherwise.
   */
  const renderStudentCount = () => {
    if (currentStudentIndex >= 0) {
      return (
        <label>
          Student {`${currentStudentIndex + 1} of ${students.length}`}
        </label>
      );
    } else {
      return <label>{`${students.length} Students`}</label>;
    }
  };

  /**
   * Callback to set the current selected student.
   */
  const onSelectStudent = studentIndex => {
    setCurrentStudentIndex(studentIndex);
  };

  /**
   * Return the current student, or an empty object if there is none
   */
  const getCurrentStudent = () => {
    return students[currentStudentIndex] ? students[currentStudentIndex] : {};
  };

  return (
    <div className="LMSGrader">
      <header>
        <ul className="LMSGrader__grading-components">
          <li className="LMSGrader__title">
            <h1 className="LMSGrader__assignment">{assignmentName}</h1>
            <h2 className="LMSGrader__name">{courseName}</h2>
          </li>
          <li className="LMSGrader__student-picker">
            <div className="LMSGrader__student-count">
              {renderStudentCount()}
            </div>
            <StudentSelector
              onSelectStudent={onSelectStudent}
              students={students}
              selectedStudentIndex={currentStudentIndex}
            />
          </li>
          <li className="LMSGrader__student-grade">
            <SubmitGradeForm
              student={getCurrentStudent()}
              disabled={currentStudentIndex < 0}
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

  // Assignment and course information
  courseName: propTypes.string.isRequired,
  assignmentName: propTypes.string.isRequired,

  // Callback to alert the parent component that a change has occurred and re-rendering may be needed.
  onChangeSelectedUser: propTypes.func.isRequired,

  // List of students to grade
  students: propTypes.array.isRequired,
};
