import { APIError } from '../../utils/api';
import { VitalSourceService } from '../vitalsource';

describe('VitalSourceService', () => {
  describe('#fetchBooks', () => {
    it('returns book data', async () => {
      const service = new VitalSourceService({ authToken: 'dummy-token' });
      const data = await service.fetchBooks(1 /* delay */);
      assert.isTrue(Array.isArray(data));
      assert.equal(data.length, 2);
    });
  });

  describe('#fetchChapters', () => {
    it('returns chapter list', async () => {
      const service = new VitalSourceService({ authToken: 'dummy-token' });
      const data = await service.fetchChapters(
        'BOOKSHELF-TUTORIAL',
        1 /* delay */
      );
      assert.isTrue(Array.isArray(data));
      assert.equal(data.length, 45);
    });

    it('throws if book ID is unknown', async () => {
      const service = new VitalSourceService({ authToken: 'dummy-token' });
      let err;
      try {
        await service.fetchChapters('unknown-book-id', 1 /* delay */);
      } catch (e) {
        err = e;
      }
      assert.instanceOf(err, APIError);
      assert.equal(err.message, 'Book not found');
    });
  });
});
