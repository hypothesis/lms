// Expose sinon assertions.
sinon.assert.expose(assert, { prefix: null });

// Configure Enzyme for UI tests.
require('preact/debug');
import { patchPropTypes } from './frontend_apps/utils/prop-types';
import propTypes from 'prop-types';
patchPropTypes(propTypes);

import { configure } from 'enzyme';
import { Adapter } from 'enzyme-adapter-preact-pure';
configure({ adapter: new Adapter() });
