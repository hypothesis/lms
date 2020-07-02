import { apiCall } from './api';

/**
 * @typedef {Object} Student
 * @prop {string} LISResultSourcedId - Unique outcome identifier
 * @prop {string} LISOutcomeServiceUrl - API URL for posting outcome results
 */

/**
 * The fetched grade success result.
 *
 * @typedef {Object} FetchGradeResult
 * @prop {number} currentScore - The fetched grade
 */

/**
 * Submits a student's grade to the LTI endpoint.
 *
 * @param {Object} options
 * @param {Student} options.student - Student object
 * @param {number} options.grade - A number between 0 and 1
 * @param {string} options.authToken - The auth token from the config
 */
function submitGrade({ student, grade, authToken }) {
  return apiCall({
    authToken,
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
 * @param {Object} options
 * @param {Student} options.student - Student object
 * @param {string} options.authToken - The auth token from the config
 * @return {Promise<FetchGradeResult>}
 */
function fetchGrade({ student, authToken }) {
  return apiCall({
    authToken,
    path: `/api/lti/result?lis_result_sourcedid=${student.LISResultSourcedId}&lis_outcome_service_url=${student.LISOutcomeServiceUrl}`,
  });
}
export { fetchGrade, submitGrade };
