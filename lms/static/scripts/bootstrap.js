import * as testUtils from 'preact/test-utils';
import { options } from 'preact';

// Expose sinon assertions.
sinon.assert.expose(assert, { prefix: null });

// Configure Enzyme for UI tests.
require('preact/debug');
import { configure } from 'enzyme';
import { Adapter } from 'enzyme-adapter-preact-pure';
configure({ adapter: new Adapter() });

// Work around https://github.com/preactjs/preact/issues/1681.
// Replace `act` function from `preact/test-utils` with a version which restores
// `options.debounceRendering` afterwards.
const originalAct = testUtils;
testUtils.act = callback => {
  const debounceRendering = options.debounceRendering;
  originalAct(callback);
  options.debounceRendering = debounceRendering;
};
