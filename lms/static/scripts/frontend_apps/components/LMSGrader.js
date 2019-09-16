import { createElement } from 'preact';
import propTypes from 'prop-types';
import { useContext, useState } from 'preact/hooks';

import { Config } from '../config';
import StudentsSelector from './StudentsSelector';

/**
 * The LMS Grader menu that is fixed at the top of the page. This menu shows which assignment is currently
 * active as well as a list of students to both view and submit grades for.
 *
 * WIP component.
 */

export default function LMSGrader({ children, onChangeUser }) {
  const { grading } = useContext(Config);
  const students = grading.students;

  // Initial current student is the first in the list
  const [currentStudent, setCurrentStudent] = useState(0);

  // Reference to the sidebar config DOM node
  const sidebarConfigEl = document.querySelector('.js-hypothesis-config');

  // Editable sidebar config object
  const sidebarConfig = JSON.parse(sidebarConfigEl.text);

  /**
   * Sets the focus mode config object to a target student.
   *
   * @param {*} student - Array of students
   */

  const setFocusedStudentConfig = student => {
    if (student) {
      if (!sidebarConfig.focus) {
        sidebarConfig.focus = {};
      }
      sidebarConfig.focus = {
        ...sidebarConfig.focus,
        user: {
          username: student.username,
          displayName: student.displayName,
        },
      };
      sidebarConfigEl.text = JSON.stringify(sidebarConfig);
    }
  };

  // Initially set the focused student sidebar config
  setFocusedStudentConfig(students[currentStudent]);

  /**
   * Main handler function to perform any state updates
   * required change a focused user.
   */
  const onSelectStudent = studentIndex => {
    setFocusedStudentConfig(students[studentIndex]);
    setCurrentStudent(studentIndex);
    onChangeUser(students[studentIndex].username);
  };

  /*
  function submitGrade(grade) {
    // todo
  }
  */

  return (
    <header className="LMSGrader">
      <ul>
        <li className="LMSGrader__course-assignment">
          <h2>Course Name</h2>
          <h3>Assignment Name</h3>
        </li>
        <li className="LMSGrader__student-index">
          <span>{`${currentStudent + 1}/${students.length}`}</span>
        </li>
        <li className="LMSGrader__student-picker">
          <StudentsSelector
            onSelectStudent={onSelectStudent}
            students={students}
            selectedStudentIndex={currentStudent}
          />
        </li>
      </ul>
      {children}
    </header>
  );
}

LMSGrader.propTypes = {
  // Callback to alert the parent component that a change has occurred and re-rendering may be needed.
  onChangeUser: propTypes.func.isRequired,

  // <iframe> to pass along
  children: propTypes.node.isRequired,
};
