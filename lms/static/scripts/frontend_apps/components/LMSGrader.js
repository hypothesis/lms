import { createElement } from 'preact';
import { useCallback, useEffect, useMemo, useState } from 'preact/hooks';

import StudentSelector from './StudentSelector';
import SubmitGradeForm from './SubmitGradeForm';

/**
 * @typedef {import('../config').StudentInfo} StudentInfo
 * @typedef {import('../services/client-rpc').ClientRpc} ClientRpc
 */

/**
 * @typedef LMSGraderProps
 * @prop {Object} children - The <iframe> element displaying the assignment
 * @prop {ClientRpc} clientRpc - Service for communicating with Hypothesis client
 * @prop {string} courseName
 * @prop {string} assignmentName
 * @prop {StudentInfo[]} students - List of students to grade
 */

/**
 * The LMSGrader component is fixed at the top of the page. This toolbar shows which assignment is currently
 * active as well as a list of students to both view and submit grades for.
 *
 * @param {LMSGraderProps} props
 */
export default function LMSGrader({
  children,
  clientRpc,
  assignmentName,
  courseName,
  students: unorderedStudents,
}) {
  // No initial current student selected
  const [currentStudentIndex, setCurrentStudentIndex] = useState(-1);

  // Students sorted by displayName
  const students = useMemo(() => {
    function compareNames(name1 = '', name2 = '') {
      if (name1.toLowerCase() < name2.toLowerCase()) {
        return -1;
      } else if (name1.toLowerCase() > name2.toLowerCase()) {
        return 1;
      } else {
        return 0;
      }
    }
    // Make a copy
    const students_ = [...unorderedStudents];

    students_.sort((student1, student2) => {
      return compareNames(student1.displayName, student2.displayName);
    });
    return students_;
  }, [unorderedStudents]);

  /**
   * Makes an RPC call to the sidebar to change to the focused user.
   */
  const changeFocusedUser = useCallback(
    /** @param {StudentInfo|null} user - The user to focus on in the sidebar */
    user => clientRpc.setFocusedUser(user),
    [clientRpc]
  );

  useEffect(() => {
    if (currentStudentIndex >= 0) {
      changeFocusedUser(students[currentStudentIndex]);
    } else {
      changeFocusedUser(null);
    }
  }, [students, changeFocusedUser, currentStudentIndex]);

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
   *
   * @param {number} studentIndex
   */
  const onSelectStudent = studentIndex => {
    setCurrentStudentIndex(studentIndex);
  };

  /**
   * Return the current student, or an empty object if there is none
   */
  const getCurrentStudent = () => {
    return currentStudentIndex >= 0 ? students[currentStudentIndex] : null;
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
            <SubmitGradeForm student={getCurrentStudent()} />
          </li>
        </ul>
      </header>
      {children}
    </div>
  );
}
