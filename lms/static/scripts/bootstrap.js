import { act } from 'preact/test-utils';
import { options } from 'preact';

// Expose sinon assertions.
sinon.assert.expose(assert, { prefix: null });

// Configure Enzyme for UI tests.
require('preact/debug');
import { configure } from 'enzyme';
import { Adapter } from 'enzyme-adapter-preact-pure';
configure({ adapter: new Adapter() });

// Work around https://github.com/preactjs/preact/issues/1681.
// Run `act` which replaces `options.debounceRendering`, then replace it
// with a fixed version and prevent that fixed version from being overwritten
// later.
act(() => {});
const debounceRendering = options.debounceRendering;
const fixedDebounceRendering = callback => {
  debounceRendering(callback);
  setTimeout(callback);
};
Object.defineProperty(options, 'debounceRendering', {
  get: () => fixedDebounceRendering,
  set: () => {
    /* make attempts to update this a no-op */
  },
});
