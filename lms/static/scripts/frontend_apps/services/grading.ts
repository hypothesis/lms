import { apiCall } from '../utils/api';

export type Student = {
  /** Unique outcome identifier. */
  LISResultSourcedId: string;

  /** API URL for posting outcome results. */
  LISOutcomeServiceUrl: string;

  /** LTI user id for this student. */
  lmsId: string;
};

/**
 * The fetched grade success result.
 */
export type FetchGradeResult = {
  currentScore?: number | null;
};

/**
 * Service for fetching and submitting student grades for an assignment.
 */
export class GradingService {
  private _authToken: string;

  constructor({ authToken }: { authToken: string }) {
    this._authToken = authToken;
  }

  /**
   * Submits a student's grade to the LTI endpoint.
   */
  submitGrade({ student, grade }: { student: Student; grade: number }) {
    return apiCall<void>({
      authToken: this._authToken,
      path: '/api/lti/result',
      data: {
        lis_result_sourcedid: student.LISResultSourcedId,
        lis_outcome_service_url: student.LISOutcomeServiceUrl,
        student_user_id: student.lmsId,
        score: grade,
      },
    });
  }

  /**
   * Fetches a student's grade from the LTI endpoint.
   */
  async fetchGrade({
    student,
  }: {
    student: Student;
  }): Promise<FetchGradeResult> {
    return apiCall<FetchGradeResult>({
      authToken: this._authToken,
      path: '/api/lti/result',
      params: {
        lis_result_sourcedid: student.LISResultSourcedId,
        lis_outcome_service_url: student.LISOutcomeServiceUrl,
      },
    });
  }
}
