import { fetchGrade, submitGrade, $imports } from '../grader-service';

describe('grader-services', () => {
  const fakeApiCall = sinon.stub().resolves({});

  beforeEach(() => {
    $imports.$mock({
      './api': {
        apiCall: fakeApiCall,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  context('submitGrade', () => {
    it('returns a promise', async () => {
      const result = submitGrade({
        student: {
          LISResultSourcedId: 0,
          LISOutcomeServiceUrl: 'url',
        },
        grade: 1,
        authToken: 'auth',
      });
      assert.isTrue(result instanceof Promise);
    });

    it('calls submitGrade with the provided parameters', async () => {
      await submitGrade({
        student: {
          LISResultSourcedId: 0,
          LISOutcomeServiceUrl: 'url',
        },
        grade: 1,
        authToken: 'auth',
      });
      assert.isTrue(
        fakeApiCall.calledWithMatch({
          authToken: 'auth',
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

  context('fetchGrade', () => {
    it('returns a promise', async () => {
      const result = fetchGrade({
        student: {
          LISResultSourcedId: 0,
          LISOutcomeServiceUrl: 'url',
        },
        authToken: 'auth',
      });
      assert.isTrue(result instanceof Promise);
    });

    it('calls fetchGrade with the provided parameters', async () => {
      await submitGrade({
        student: {
          LISResultSourcedId: 0,
          LISOutcomeServiceUrl: 'url',
        },
        authToken: 'auth',
      });
      assert.isTrue(
        fakeApiCall.calledWithMatch({
          authToken: 'auth',
          path: '/api/lti/result',
          data: {
            lis_result_sourcedid: 0,
            lis_outcome_service_url: 'url',
          },
        })
      );
    });
  });
});
