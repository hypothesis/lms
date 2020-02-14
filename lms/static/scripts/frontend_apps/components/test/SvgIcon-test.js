import { createElement, render } from 'preact';

import SvgIcon from '../SvgIcon';
import { checkAccessibility } from '../../../test-util/accessibility';

describe('SvgIcon', () => {
  const inlineSvg = {
    trustedHTML: '<svg />',
  };
  const inlineSvg2 = {
    trustedHTML: '<svg width="3" class="svg2" />',
  };
  const unTrustedSvg = '<svg />';

  // Tests here use DOM APIs rather than Enzyme because SvgIcon uses
  // `dangerouslySetInnerHTML` for its content, and that is not visible in the
  // Enzyme tree.

  // Some of the tests below intentionally pass arguments of invalid types
  // as the `src` prop. Ignore the `console.error` that this triggers.
  beforeEach(() => {
    sinon.stub(console, 'error');
  });

  afterEach(() => {
    console.error.restore();
  });

  it("sets the element's content to the content of the SVG", () => {
    const container = document.createElement('div');
    render(<SvgIcon src={inlineSvg} />, container);
    assert.ok(container.querySelector('svg'));
  });

  it('throws an error if the icon is unknown', () => {
    assert.throws(() => {
      const container = document.createElement('div');
      render(<SvgIcon />, container);
    });
  });

  it('throws an error if the icon is un-trusted svg', () => {
    assert.throws(() => {
      const container = document.createElement('div');
      render(<SvgIcon src={unTrustedSvg} />, container);
    });
  });

  it('does not set the class of the SVG by default', () => {
    const container = document.createElement('div');
    render(<SvgIcon src={inlineSvg} />, container);
    const svg = container.querySelector('svg');
    assert.equal(svg.getAttribute('class'), '');
  });

  it('sets the class of the SVG if provided', () => {
    const container = document.createElement('div');
    render(<SvgIcon src={inlineSvg} className="thing__icon" />, container);
    const svg = container.querySelector('svg');
    assert.equal(svg.getAttribute('class'), 'thing__icon');
  });

  it('retains the CSS class if the icon changes', () => {
    const container = document.createElement('div');
    render(<SvgIcon src={inlineSvg} className="thing__icon" />, container);
    render(<SvgIcon src={inlineSvg2} className="thing__icon" />, container);
    const svg = container.querySelector('svg');
    assert.equal(svg.getAttribute('class'), 'thing__icon');
  });

  it('sets a default class on the wrapper element', () => {
    const container = document.createElement('div');
    render(<SvgIcon src={inlineSvg} />, container);
    const wrapper = container.querySelector('span');
    assert.isTrue(wrapper.classList.contains('svg-icon'));
    assert.isFalse(wrapper.classList.contains('svg-icon--inline'));
  });

  it('appends an inline class to wrapper if `inline` prop is `true`', () => {
    const container = document.createElement('div');
    render(<SvgIcon inline={true} src={inlineSvg} />, container);
    const wrapper = container.querySelector('span');
    assert.isTrue(wrapper.classList.contains('svg-icon'));
    assert.isTrue(wrapper.classList.contains('svg-icon--inline'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      // eslint-disable-next-line react/display-name
      content: () => <SvgIcon src={inlineSvg} />,
    })
  );
});
