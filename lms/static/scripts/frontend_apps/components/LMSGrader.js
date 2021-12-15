import {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'preact/hooks';

import { apiCall } from '../utils/api';
import { Config } from '../config';

import StudentSelector from './StudentSelector';
import SubmitGradeForm from './SubmitGradeForm';
import classnames from 'classnames';

/**
 * @typedef {import('../config').StudentInfo} StudentInfo
 * @typedef {import('../services/client-rpc').ClientRPC} ClientRPC
 */

/**
 * @typedef LMSGraderProps
 * @prop {object} children - The <iframe> element displaying the assignment
 * @prop {ClientRPC} clientRPC - Service for communicating with Hypothesis client
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
  clientRPC,
  assignmentName,
  courseName,
  students: unorderedStudents,
}) {
  const {
    api: { authToken, sync: syncAPICallInfo },
  } = useContext(Config);

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
    async user => {
      let groups = null;
      if (syncAPICallInfo && user?.lmsId) {
        // Request and set a list of groups specific to the student being graded
        const studentGroupsCallData = {
          ...syncAPICallInfo.data,
          gradingStudentId: user.lmsId,
        };
        try {
          groups = await apiCall({
            authToken,
            path: syncAPICallInfo.path,
            data: studentGroupsCallData,
          });
        } catch (e) {
          // TODO: Improved error handling
          console.error('Unable to fetch student groups from sync API');
        }
      }
      clientRPC.setFocusedUser(user, groups);
    },
    [authToken, clientRPC, syncAPICallInfo]
  );

  useEffect(() => {
    if (currentStudentIndex >= 0) {
      changeFocusedUser(students[currentStudentIndex]);
    } else {
      changeFocusedUser(null);
    }
  }, [students, changeFocusedUser, currentStudentIndex]);

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
    <>
      <header
        className={classnames(
          'grid grid-cols-1 items-center gap-y-2 p-2',
          'lg:grid-cols-3 lg:gap-x-4 lg:px-3'
        )}
      >
        <div>
          <h1 className="text-lg p-0 m-0" data-testid="assignment-name">
            {assignmentName}
          </h1>
          <h2
            className="text-base font-medium p-0 m-0"
            data-testid="course-name"
          >
            {courseName}
          </h2>
        </div>

        <div
          className={classnames(
            'flex flex-col gap-2',
            'sm:flex-row',
            'lg:col-span-2 lg:gap-4 ' /* cols 2-3 of 3 */
          )}
        >
          <div className="flex-grow-0 sm:flex-grow">
            <StudentSelector
              onSelectStudent={onSelectStudent}
              students={students}
              selectedStudentIndex={currentStudentIndex}
            />
          </div>
          <div className="flex-grow sm:flex-grow-0">
            <SubmitGradeForm student={getCurrentStudent()} />
          </div>
        </div>
      </header>
      {children}
    </>
  );
}
