import { assumeUTC } from '../date';

describe('assumeUTC', () => {
  [
    // Naive datetimes are assumed to be UTC.
    ['2026-07-08T23:59:29', '2026-07-08T23:59:29Z'],
    ['2026-07-08T23:59:29.622705', '2026-07-08T23:59:29.622705Z'],
    // Datetimes with an explicit offset or "Z" are returned unchanged.
    ['2026-07-08T23:59:29.622705+00:00', '2026-07-08T23:59:29.622705+00:00'],
    ['2026-07-08T20:59:29-03:00', '2026-07-08T20:59:29-03:00'],
    ['2026-07-08T23:59:29Z', '2026-07-08T23:59:29Z'],
  ].forEach(([input, expected]) => {
    it(`normalizes ${input}`, () => {
      assert.equal(assumeUTC(input), expected);
    });

    it(`produces a string that Date can parse (${input})`, () => {
      assert.isFalse(isNaN(new Date(assumeUTC(input)).valueOf()));
    });
  });
});
