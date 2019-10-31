import { apiCall } from './api';

/**
 * @typedef {Object} Student
 * @prop {string} LISResultSourcedId - The unique student id
 * @prop {string} LISOutcomeServiceUrl - The student's service url
 */

/**
 * The fetched grade result
 *
 * @typedef {Promise<Object>} FetchGradeResult
 * @prop {number} currentScore - The fetched grade
 */

/**
 * The submitted grade result
 *
 * @typedef {Promise<Object>} SubmitGradeResult
 */

/**
 * Submits a student's grade to the LTI endpoint.
 *
 * @param {Student} student - Student object
 * @param {number} grade - A number between 0 and 1
 * @param {string} authToken - The auth token from the config
 * @return {SubmitGradeResult}
 *
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
 * @param {Student} student - Student object
 * @param {string} authToken - The auth token from the config
 * @return {FetchGradeResult>} - The fetched result
 *
 */
function fetchGrade({ student, authToken }) {
  return apiCall({
    authToken,
    path: `/api/lti/result?lis_result_sourcedid=${student.LISResultSourcedId}&lis_outcome_service_url=${student.LISOutcomeServiceUrl}`,
  });
}
export { fetchGrade, submitGrade };
