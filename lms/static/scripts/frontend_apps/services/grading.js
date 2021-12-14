import { apiCall } from '../utils/api';

/**
 * @typedef Student
 * @prop {string} LISResultSourcedId - Unique outcome identifier
 * @prop {string} LISOutcomeServiceUrl - API URL for posting outcome results
 */

/**
 * The fetched grade success result.
 *
 * @typedef FetchGradeResult
 * @prop {number|null} currentScore - The fetched grade
 */

/**
 * Service for fetching and submitting student grades for an assignment.
 */
export class GradingService {
  /**
   * @param {object} options
   *   @param {string} options.authToken
   */
  constructor({ authToken }) {
    this._authToken = authToken;
  }

  /**
   * Submits a student's grade to the LTI endpoint.
   *
   * @param {object} options
   *   @param {Student} options.student
   *   @param {number} options.grade - A number between 0 and 1
   * @return {Promise<void>}
   */
  submitGrade({ student, grade }) {
    return apiCall({
      authToken: this._authToken,
      path: '/api/lti/result',
      data: {
        lis_result_sourcedid: student.LISResultSourcedId,
        lis_outcome_service_url: student.LISOutcomeServiceUrl,
        score: grade,
      },
    });
  }

  /**
   * Fetches a student's grade from the LTI endpoint
   *
   * @param {object} options
   *   @param {Student} options.student - Student object
   * @return {Promise<FetchGradeResult>}
   */
  async fetchGrade({ student }) {
    const result = await apiCall({
      authToken: this._authToken,
      path: '/api/lti/result',
      params: {
        lis_result_sourcedid: student.LISResultSourcedId,
        lis_outcome_service_url: student.LISOutcomeServiceUrl,
      },
    });
    return /** @type {FetchGradeResult} */ (result);
  }
}
