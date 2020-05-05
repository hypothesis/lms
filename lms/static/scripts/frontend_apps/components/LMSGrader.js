import { createElement } from 'preact';
import propTypes from 'prop-types';
import { useEffect, useState } from 'preact/hooks';

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

  /**
   * Create a name object for a given displayName for a
   * student to facilitate sorting. This object contains
   * a firstName and optional lastName as well as a new
   * displayName as "{last}, {first}"
   *
   * @return {object}
   * e.g.
   * {
   *  displayName: <string>
   *  firstName: <string>
   *  lastName: <string|null>
   * }
   */
  const makeNames = name => {
    const parts = name.split(' ');
    if (parts.length <= 1) {
      // No separator, don't mutate displayName
      return {
        displayName: name,
        firstName: name,
        lastName: null,
      };
    } else {
      const first = parts[0];
      // If there is more than two separators, just lump any beyond
      // the first into the last name.
      const last = parts.slice(1).join(' ');
      let displayName;
      if (last) {
        displayName = `${last}, ${first}`;
      } else {
        displayName = first;
      }
      return {
        displayName,
        firstName: first,
        lastName: last,
      };
    }
  };

  // A sorted list of students. Students are sorted by
  //  1. last name
  //  2. first name
  // Not all students may have a last name and in which
  // case their first name is used to sort by.
  const [students] = useState(() => {
    // First, create a first and last name for each student
    // so we can compare on those values.
    const students_ = unorderedStudents.map(s => {
      return {
        ...s,
        ...makeNames(s.displayName),
      };
    });
    students_.sort((student1, student2) => {
      function compareNames(name1, name2) {
        if (name1.toLowerCase() < name2.toLowerCase()) {
          return -1;
        } else if (name1.toLowerCase() > name2.toLowerCase()) {
          return 1;
        } else {
          return 0;
        }
      }
      // Compare last name, then first name. If there is no last name
      // then compare first name.
      let result = compareNames(
        student1.lastName ? student1.lastName : student1.firstName,
        student2.lastName ? student2.lastName : student2.firstName
      );
      if (result === 0) {
        // Tie breaker (if needed)
        // If we previously compared on first name, then the second compare
        // shall use an empty string, otherwise use the first name.
        result = compareNames(
          student1.lastName ? student1.firstName : '',
          student2.lastName ? student2.firstName : ''
        );
      }
      return result;
    });
    return students_;
  });

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
