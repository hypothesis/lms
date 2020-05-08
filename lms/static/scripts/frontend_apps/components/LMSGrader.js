import { createElement } from 'preact';
import propTypes from 'prop-types';
import { useEffect, useMemo, useState } from 'preact/hooks';

import { call as rpcCall } from '../../postmessage_json_rpc/client';
import { getSidebarWindow } from '../../postmessage_json_rpc/server';

import StudentSelector from './StudentSelector';
import SubmitGradeForm from './SubmitGradeForm';

/**
 * The LMSGrader component is fixed at the top of the page. This toolbar shows which assignment is currently
 * active as well as a list of students to both view and submit grades for.
 */

export default function LMSGrader({
  children,
  assignmentName,
  courseName,
  students: unorderedStudents,
}) {
  // No initial current student selected
  const [currentStudentIndex, setCurrentStudentIndex] = useState(-1);

  // A sorted list of students. Students are sorted by
  // displayName.
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
   *
   * @param {User} user - The user to focus on in the sidebar
   */
  const changeFocusedUser = async user => {
    const sidebar = await getSidebarWindow();
    // Calls the client sidebar to fire the `changeFocusModeUser` action
    // to change the focused user.
    rpcCall(sidebar.frame, sidebar.origin, 'changeFocusModeUser', [
      {
        username: user.userid, // change `username` key to `userid` once the client is ready
        displayName: user.displayName,
      },
    ]);
  };

  useEffect(() => {
    if (students[currentStudentIndex]) {
      changeFocusedUser(students[currentStudentIndex]);
    } else {
      changeFocusedUser({}); // any non-real userid will clear out a previously focused user
    }
  }, [students, currentStudentIndex]);

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
  // List of students to grade
  students: propTypes.array.isRequired,
};
