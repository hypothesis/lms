import classnames from 'classnames';
import { useCallback, useEffect, useMemo, useState } from 'preact/hooks';

import { apiCall } from '../utils/api';
import { useConfig } from '../config';
import type { StudentInfo } from '../config';
import { ClientRPC, useService } from '../services';
import StudentSelector from './StudentSelector';
import SubmitGradeForm from './SubmitGradeForm';

/**
 * Controls for grading students: a list of students to grade, and an input to
 * set a grade for the selected student.
 */
export default function GradingControls() {
  const {
    api: { authToken, sync: syncAPICallInfo },
    grading,
  } = useConfig();

  const clientRPC = useService(ClientRPC);

  const unorderedStudents = grading?.students;

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
    const students_ = unorderedStudents ? [...unorderedStudents] : [];

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
    <div className={classnames('flex flex-col gap-2', 'sm:flex-row')}>
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
  );
}
