import { ContentInfoFetcher, $imports } from '../content-info-fetcher';

describe('ContentInfoFetcher', () => {
  const fakeAuthToken = 'abcdef123';
  let fakeAPICall;
  let fakeClientRPC;

  beforeEach(() => {
    fakeAPICall = sinon.stub().resolves({ title: 'Test article' });
    fakeClientRPC = {
      showContentInfo: sinon.stub().resolves(),
    };

    $imports.$mock({
      '../utils/api': {
        apiCall: fakeAPICall,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  describe('#fetch', () => {
    it('fetches article metadata and sends it to client', async () => {
      const fetcher = new ContentInfoFetcher(fakeAuthToken, fakeClientRPC);

      await fetcher.fetch({ source: 'jstor', itemId: '123456' });

      assert.calledWith(fakeAPICall, {
        authToken: fakeAuthToken,
        path: '/api/jstor/articles/123456',
      });

      assert.calledWith(fakeClientRPC.showContentInfo, {
        logo: {
          logo: new URL(
            '/static/images/jstor-logo.svg',
            location.href
          ).toString(),
          title: 'JSTOR homepage',
          link: 'https://www.jstor.org',
        },
        item: {
          title: 'Test article',
          containerTitle: '',
        },

        links: {},
      });
    });

    it('reports an error if content source is unknown', async () => {
      const fetcher = new ContentInfoFetcher(fakeAuthToken, fakeClientRPC);

      let error;
      try {
        await fetcher.fetch({ source: 'invalid', itemId: '123456' });
      } catch (e) {
        error = e;
      }

      assert.instanceOf(error, Error);
      assert.equal(error.message, 'Unknown content source');
    });
  });
});
