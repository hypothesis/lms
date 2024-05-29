import { clearFormatters, formatDateTime } from '../date';

describe('date', () => {
  let sandbox;

  beforeEach(() => {
    sandbox = sinon.createSandbox();
    sandbox.useFakeTimers();

    // Clear the formatters cache so that mocked formatters
    // from one test run don't affect the next.
    clearFormatters();
  });

  afterEach(() => {
    sandbox.restore();
  });

  describe('formatDateTime', () => {
    // Normalize "special" spaces (eg. "\u202F") to standard spaces.
    function normalizeSpaces(str) {
      return str.normalize('NFKC');
    }

    it('returns absolute formatted date', () => {
      const date = new Date('2020-05-04T23:02:01');
      const fakeIntl = locale => ({
        DateTimeFormat: function (_, options) {
          return new Intl.DateTimeFormat(locale, options);
        },
      });

      assert.equal(
        normalizeSpaces(formatDateTime(date, fakeIntl('en-US'))),
        'May 04, 2020, 11:02 PM',
      );

      clearFormatters();

      assert.equal(
        normalizeSpaces(formatDateTime(date, fakeIntl('de-DE'))),
        '04. Mai 2020, 23:02',
      );
    });
  });
});
