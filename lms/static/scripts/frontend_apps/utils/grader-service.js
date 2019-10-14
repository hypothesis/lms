import { apiCall } from './api';

/**
 * Submits the grade to the LTI endpoint, waits for it to return, then updates the state with the
 * new grade
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

export { submitGrade };
