import { unmountAll } from '@hypothesis/frontend-testing';
import { assert } from 'chai';
import { configure } from 'enzyme';
import { Adapter } from 'enzyme-adapter-preact-pure';
import 'preact/debug';
import sinon from 'sinon';

// Expose sinon assertions.
sinon.assert.expose(assert, { prefix: null });

// Expose these globally
globalThis.assert = assert;
globalThis.sinon = sinon;
globalThis.context ??= globalThis.describe;

// Configure Enzyme for UI tests.
configure({ adapter: new Adapter() });
afterEach(() => {
  unmountAll();
});
