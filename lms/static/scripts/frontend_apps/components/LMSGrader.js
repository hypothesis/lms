import { createElement } from 'preact';
import propTypes from 'prop-types';
import { useContext, useState } from 'preact/hooks';

import { Config } from '../config';
import StudentsSelector from './StudentsSelector';

/**
 * The LMS Grader menu that is fixed at the top of the page. This menu shows which assignment is currently
 * active as well as a list of students to both view and submit grades for.
 *
 * This is component is still a WIP.
 */

export default function LMSGrader({ children }) {
  const {
    students,
    //course,
    //assignment,
  } = useContext(Config);

  const [currentStudent, set_currentStudent] = useState(0);

  const onNextStudent = () => {
    if (currentStudent + 1 < students.length) {
      set_currentStudent(currentStudent + 1);
    }
  };
  const onPrevStudent = () => {
    if (currentStudent > 0) {
      set_currentStudent(currentStudent - 1);
    }
  };

  const hasNextStudent = currentStudent + 1 < students.length;
  const hasPrevStudent = currentStudent > 0;

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
            onPrevStudent={onPrevStudent}
            onNextStudent={onNextStudent}
            hasNextStudent={hasNextStudent}
            hasPrevStudent={hasPrevStudent}
            student={students[currentStudent]}
          />
        </li>
      </ul>
      {children}
    </header>
  );
}

LMSGrader.propTypes = {
  children: propTypes.node.isRequired,
};
