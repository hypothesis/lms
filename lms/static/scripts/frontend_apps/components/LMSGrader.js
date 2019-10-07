import { createElement } from 'preact';
import { useContext, useEffect, useState } from 'preact/hooks';
import propTypes from 'prop-types';

import { Config } from '../config';
import ErrorDialog from './ErrorDialog';
import Spinner from './Spinner';
import StudentSelector from './StudentSelector';
import SubmitGradeForm from './SubmitGradeForm';
import { apiCall } from '../utils/api';
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
  students,
  onChangeSelectedUser,
}) {
  // No initial current student selected
  const [currentStudentIndex, setCurrentStudentIndex] = useState(-1);
  const [grade, setGrade] = useState(''); // TODO: set this on a fetch @ loadtime

  const [networkError, setNetworkError] = useState(''); // if there is an error when submitting grade
  const [requestStatus, setRequestStatus] = useState(''); // ajax request state, one of ('', 'fetching', 'error', 'done')

  const { authToken } = useContext(Config);

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
    setRequestStatus('');
    setCurrentStudentIndex(studentIndex);
    // TODO, query student grade
    setGrade('');
  };

  /**
   * Submits the grade to the LTI endpoint, waits for it to return, then updates the state with the
   * new grade
   *
   * @param {Number} grade
   */
  const submitGrade = async grade => {
    try {
      setRequestStatus('fetching');
      await apiCall({
        authToken,
        path: '/api/lti/result',
        data: {
          lis_result_sourcedid:
            students[currentStudentIndex].LISResultSourcedId,
          lis_outcome_service_url:
            students[currentStudentIndex].LISOutcomeServiceUrl,
          score: grade / 10, // scale the grade for the LTI endpoint, grade must be a numeric type.
        },
      });
      setGrade(grade); // update local state on success
      setRequestStatus('done');
    } catch (e) {
      setRequestStatus('error');
      if (e.errorMessage) {
        setNetworkError(e.errorMessage);
      } else {
        setNetworkError('Unknown error');
      }
    }
  };

  return (
    <div className="LMSGrader">
      <header>
        <ul className="LMSGrader__grading-components">
          <li className="LMSGrader__assignment">
            {
              // placeholder for course name and assignment
            }
          </li>
          <li className="LMSGrader__grading-components--label-wrapper">
            {renderStudentCount()}
          </li>
          <li className="LMSGrader__student-picker">
            <StudentSelector
              onSelectStudent={onSelectStudent}
              students={students}
              selectedStudentIndex={currentStudentIndex}
            />
          </li>
          <li className="LMSGrader__student-grade">
            <SubmitGradeForm
              studentGrade={grade}
              onSubmitGrade={submitGrade}
              key={currentStudentIndex}
              disabled={currentStudentIndex < 0}
              gradeSaved={requestStatus === 'done'}
            />
          </li>
        </ul>
        {requestStatus === 'error' && (
          <ErrorDialog
            title="Error"
            error={{ message: networkError }}
            onCancel={() => {
              setRequestStatus('');
            }}
          />
        )}
        {requestStatus === 'fetching' && (
          <div className="LMSGrader__loading-backdrop">
            <Spinner className="LMSGrader__spinner" />
          </div>
        )}
      </header>
      {children}
    </div>
  );
}

LMSGrader.propTypes = {
  // iframe to pass along
  children: propTypes.node.isRequired,
  // Callback to alert the parent component that a change has occurred and re-rendering may be needed.
  onChangeSelectedUser: propTypes.func.isRequired,
  // List of students to grade
  students: propTypes.array.isRequired,
};
