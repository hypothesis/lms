import { confirm } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useEffect, useMemo, useState } from 'preact/hooks';

import { useConfig } from '../config';
import type { StudentInfo } from '../config';
import { ClientRPC, useService } from '../services';
import { apiCall } from '../utils/api';
import StudentSelector from './StudentSelector';
import SubmitGradeForm from './SubmitGradeForm';

export type GradingControlsProps = {
  students: StudentInfo[];
  scoreMaximum?: number;
  acceptComments?: boolean;
};

/**
 * Sort an array of objects using a locale-aware string comparison. Return a
 * copy of `items`, sorted by the `key` property.
 */
function localeSort<Item>(items: Item[], key: keyof Item): Item[] {
  const collator = new Intl.Collator(undefined /* use default locale */, {
    sensitivity: 'accent',
  });
  return [...items].sort((a, b) =>
    collator.compare(a[key] as string, b[key] as string),
  );
}

/**
 * Controls for grading students: a list of students to grade, and an input to
 * set a grade for the selected student.
 */
export default function GradingControls({
  students: unorderedStudents,
  scoreMaximum,
  acceptComments,
}: GradingControlsProps) {
  const {
    api: { authToken, sync: syncAPICallInfo },
  } = useConfig(['api']);

  const clientRPC = useService(ClientRPC);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<StudentInfo | null>(
    null,
  );
  const changeSelectedStudent = useCallback(
    async (newSelectedStudent: StudentInfo | null) => {
      const discardChanges =
        !hasUnsavedChanges ||
        (await confirm({
          title: 'Discard changes?',
          message: (
            <div>
              There are unsaved changes to{' '}
              <span className="font-bold">{selectedStudent?.displayName}</span>
              {"'"}s grade. Do you want to discard them?
            </div>
          ),
          confirmAction: 'Discard changes',
          cancelAction: 'Continue editing',
        }));

      if (discardChanges) {
        setSelectedStudent(newSelectedStudent);
        setHasUnsavedChanges(false);
      }
    },
    [hasUnsavedChanges, selectedStudent],
  );

  const students = useMemo(
    () => localeSort(unorderedStudents, 'displayName'),
    [unorderedStudents],
  );

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
          groups = await apiCall<string[]>({
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
    [authToken, clientRPC, syncAPICallInfo],
  );

  useEffect(() => {
    if (selectedStudent) {
      changeFocusedUser(selectedStudent);
    } else {
      changeFocusedUser(null);
    }
  }, [students, changeFocusedUser, selectedStudent]);

  return (
    <div
      className={classnames(
        // Default and narrower screens: controls are stacked vertically
        'flex gap-x-4 gap-y-2 flex-col',
        // Wider screens: controls are in a single row
        'md:flex-row',
      )}
    >
      <div>
        <StudentSelector
          onSelectStudent={changeSelectedStudent}
          students={students}
          selectedStudent={selectedStudent}
        />
      </div>
      <div>
        <SubmitGradeForm
          student={selectedStudent}
          scoreMaximum={scoreMaximum}
          onUnsavedChanges={setHasUnsavedChanges}
          acceptComments={acceptComments}
        />
      </div>
    </div>
  );
}
