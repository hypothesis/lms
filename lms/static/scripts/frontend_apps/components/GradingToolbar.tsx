import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'preact/hooks';

import { apiCall } from '../utils/api';
import { Config } from '../config';
import type { StudentInfo } from '../config';
import type { ClientRPC } from '../services/client-rpc';
import StudentSelector from './StudentSelector';
import SubmitGradeForm from './SubmitGradeForm';

export type GradingToolbarProps = {
  /** Iframe element displaying assignment content. */
  children: ComponentChildren;

  /** Service for communicating with Hypothesis client. */
  clientRPC: ClientRPC;
  courseName: string;
  assignmentName: string;

  /** List of students to grade. */
  students: StudentInfo[];
};

/**
 * Toolbar which provides instructors with controls to list students who have
 * annotated this document and view/submit grades.
 */
export default function GradingToolbar({
  children,
  clientRPC,
  assignmentName,
  courseName,
  students: unorderedStudents,
}: GradingToolbarProps) {
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
    async (user: StudentInfo | null) => {
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
          // An error could plausibly occur when fetching a student's groups
          // from the sync API. This is unlikely (there are no known specific
          // use cases that would lead to an error), and the failure mode is
          // so benign — the interface would display all course groups instead
          // of this student's groups — that there is no nuanced error handling
          // here at present. This can change in the future if desired.
          // See https://github.com/hypothesis/lms/issues/3417
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

  const onSelectStudent = (studentIndex: number) => {
    setCurrentStudentIndex(studentIndex);
  };

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
        <div className="space-y-1">
          <h1
            className="text-lg font-semibold leading-none"
            data-testid="assignment-name"
          >
            {assignmentName}
          </h1>
          <h2
            className="text-sm font-normal text-color-text-light leading-none"
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
