import { createElement } from 'preact';

import { element, node } from '../prop-types';

describe('prop-types', () => {
  describe('element', () => {
    function TestComponent() {
      return null;
    }

    [<div key="foo" />, <TestComponent key="bar" />].forEach(validElement => {
      it('returns `null` passed a valid element', () => {
        const props = { aProp: validElement };
        assert.equal(element(props, 'aProp', 'TestComponent'), null);
      });
    });

    ['foo', {}, false, undefined, null].forEach(invalidElement => {
      it('returns an Error if passed an invalid element', () => {
        const props = { aProp: invalidElement };

        const result = element(props, 'aProp', 'TestComponent');

        assert.instanceOf(result, Error);
        assert.equal(
          result.message,
          'Expected prop "aProp" supplied to TestComponent to be a Preact element'
        );
      });
    });
  });

  describe('node', () => {
    [<div key="foo" />, 'test', false].forEach(validNode => {
      it('returns `null` if passed a valid node', () => {
        const props = { aProp: validNode };
        assert.equal(node(props, 'aProp', 'TestComponent'), null);
      });
    });

    [{}, undefined].forEach(invalidNode => {
      it('returns an Error if passed an invalid node', () => {
        const props = { aProp: invalidNode };

        const result = node(props, 'aProp', 'TestComponent');

        assert.instanceOf(result, Error);
        assert.equal(
          result.message,
          'Expected prop "aProp" supplied to TestComponent to be a renderable value (string, boolean, element etc.)'
        );
      });
    });
  });
});
