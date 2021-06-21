import { GradingService, $imports } from '../grading';

describe('GradingService', () => {
  let fakeAPICall;
  let gradingService;

  beforeEach(() => {
    fakeAPICall = sinon.stub().resolves({ currentScore: 5.0 });
    gradingService = new GradingService({ authToken: 'dummy-token' });

    $imports.$mock({
      '../utils/api': { apiCall: fakeAPICall },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  describe('#fetchGrade', () => {
    it('calls "GET /api/lti/result" API', async () => {
      const result = await gradingService.fetchGrade({
        student: {
          LISResultSourcedId: 'source-id',
          LISOutcomeServiceUrl: 'https://example.instructure.com/grades',
        },
      });
      assert.isTrue(
        fakeAPICall.calledWithMatch({
          authToken: 'dummy-token',
          path: '/api/lti/result',
          params: {
            lis_result_sourcedid: 'source-id',
            lis_outcome_service_url: 'https://example.instructure.com/grades',
          },
        })
      );
      assert.equal(result, await fakeAPICall.returnValues[0]);
    });
  });

  describe('#submitGrade', () => {
    it('calls "POST /api/lti/result" API', async () => {
      await gradingService.submitGrade({
        student: {
          LISResultSourcedId: 0,
          LISOutcomeServiceUrl: 'url',
        },
        grade: 1,
      });
      assert.isTrue(
        fakeAPICall.calledWithMatch({
          authToken: 'dummy-token',
          path: '/api/lti/result',
          data: {
            lis_result_sourcedid: 0,
            lis_outcome_service_url: 'url',
            score: 1,
          },
        })
      );
    });
  });
});
