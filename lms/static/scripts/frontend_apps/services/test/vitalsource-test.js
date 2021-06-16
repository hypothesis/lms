import { APIError } from '../../utils/api';
import { VitalSourceService, $imports } from '../vitalsource';

describe('VitalSourceService', () => {
  let fakeAPICall;

  beforeEach(() => {
    fakeAPICall = sinon.stub().callsFake(async ({ path, authToken }) => {
      assert.equal(authToken, 'dummy-token');

      switch (path) {
        case '/api/vitalsource/books/BOOKSHELF-TUTORIAL':
          return {
            id: 'BOOKSHELF-TUTORIAL',
            title: 'Bookshelf Tutorial',
            cover_image:
              'https://covers.vitalbook.com/vbid/BOOKSHELF-TUTORIAL/width/480',
          };
        case '/api/vitalsource/books/BOOKSHELF-TUTORIAL/toc':
          return [
            {
              title: 'Cover',
              cfi: '/6/2[;vnd.vst.idref=vst-4b4cfacf-80a2-440c-acaf-70ed8fb158f1]',
              page: '1',
            },
            {
              title: 'Welcome!',
              cfi: '/6/4[;vnd.vst.idref=vst-ae169b91-f520-449d-b99c-655767e4d0a1]',
              page: '2',
            },
          ];
        default:
          throw new APIError(400, { message: 'Book not found' });
      }
    });

    $imports.$mock({
      '../utils/api': { apiCall: fakeAPICall },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  describe('#fetchBook', () => {
    it('returns book data', async () => {
      const service = new VitalSourceService({ authToken: 'dummy-token' });
      const data = await service.fetchBook('BOOKSHELF-TUTORIAL');

      assert.hasAllKeys(data, ['id', 'title', 'cover_image']);
    });

    it('throws if a book is not found', async () => {
      const service = new VitalSourceService({ authToken: 'dummy-token' });
      let err;
      try {
        await service.fetchBook('unknown-book-id');
      } catch (e) {
        err = e;
      }
      assert.instanceOf(err, APIError);
      assert.equal(err.message, 'Book not found');
    });
  });

  describe('#fetchChapters', () => {
    it('returns chapter list', async () => {
      const service = new VitalSourceService({ authToken: 'dummy-token' });
      const data = await service.fetchChapters('BOOKSHELF-TUTORIAL');
      assert.isTrue(Array.isArray(data));
      assert.equal(data.length, 2);
    });

    it('throws if book ID is unknown', async () => {
      const service = new VitalSourceService({ authToken: 'dummy-token' });
      let err;
      try {
        await service.fetchChapters('unknown-book-id');
      } catch (e) {
        err = e;
      }
      assert.instanceOf(err, APIError);
      assert.equal(err.message, 'Book not found');
    });
  });
});
