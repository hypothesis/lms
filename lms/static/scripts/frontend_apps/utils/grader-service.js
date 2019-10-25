import { apiCall } from './api';

/**
 * Submits a student's grade to the LTI endpoint.
 *
 * @param {Object} student - Student object
 * @param {Number} grade - A number between 0 and 1
 * @param {string} authToken - The auth token from the config
 * @return {Promise<Object>} - The posted result
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
 * @param {Object} student - Student object
 * @param {string} authToken - The auth token from the config
 * @return {Promise<Object>} - The fetched result
 *
 */
function fetchGrade({ student, authToken }) {
  return apiCall({
    authToken,
    path: `/api/lti/result?lis_result_sourcedid=${student.LISResultSourcedId}&lis_outcome_service_url=${student.LISOutcomeServiceUrl}`,
  });
}
export { fetchGrade, submitGrade };
