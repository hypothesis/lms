import { rootViewTitle } from '../root-view-title';

describe('rootViewTitle', () => {
  [
    {
      config: {},
      expectedTitle: 'All courses',
    },
    {
      config: {
        organization: { name: 'University of Hypothesis' },
      },
      expectedTitle: 'University of Hypothesis',
    },
  ].forEach(({ config, expectedTitle }) => {
    it('returns expected title for provided config', () => {
      assert.equal(rootViewTitle(config), expectedTitle);
    });
  });
});
