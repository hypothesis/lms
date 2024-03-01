import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import GradingCommentButton from '../GradingCommentButton';

const noop = () => {};

describe('GradingCommentButton', () => {
  const getToggleButton = wrapper =>
    wrapper.find('Button[data-testid="comment-toggle-button"]');

  const togglePopover = wrapper =>
    getToggleButton(wrapper).find('button').simulate('click');

  const commentPopoverExists = wrapper =>
    wrapper.exists('[data-testid="comment-popover"]');

  const renderComponent = (props = {}) =>
    mount(
      <GradingCommentButton
        comment="Good job!"
        disabled={false}
        loading={false}
        onSubmit={noop}
        onInput={noop}
        {...props}
      />,
    );

  it('allows comment popover to be toggled', () => {
    const wrapper = renderComponent();

    // Popover is initially hidden
    assert.isFalse(commentPopoverExists(wrapper));
    assert.isFalse(getToggleButton(wrapper).prop('expanded'));

    // Clicking the toggle will display the popover
    togglePopover(wrapper);
    assert.isTrue(commentPopoverExists(wrapper));
    assert.isTrue(getToggleButton(wrapper).prop('expanded'));

    // A second click will hide the popover
    togglePopover(wrapper);
    assert.isFalse(commentPopoverExists(wrapper));
    assert.isFalse(getToggleButton(wrapper).prop('expanded'));
  });

  it('hides the popover when `Escape` is pressed', () => {
    const wrapper = renderComponent();

    // Show popover
    togglePopover(wrapper);
    assert.isTrue(commentPopoverExists(wrapper));

    document.body.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Escape' }),
    );
    wrapper.update();

    assert.isFalse(commentPopoverExists(wrapper));
  });

  it('hides the popover when clicking away', () => {
    const wrapper = renderComponent();

    // Show popover
    togglePopover(wrapper);
    assert.isTrue(commentPopoverExists(wrapper));

    const externalButton = document.createElement('button');
    document.body.append(externalButton);
    externalButton.click();
    wrapper.update();

    try {
      assert.isFalse(commentPopoverExists(wrapper));
    } finally {
      // Make sure this button is removed even if the assert fails
      externalButton.remove();
    }
  });

  [
    { loading: true, comment: '', expectedTitle: 'Add comment' },
    { loading: false, comment: '', expectedTitle: 'Add comment' },
    { loading: true, comment: 'A comment', expectedTitle: 'Add comment' },
    { loading: false, comment: 'A comment', expectedTitle: 'Edit comment' },
  ].forEach(({ comment, loading, expectedTitle }) => {
    it('adds proper title to toggle button based on provided props', async () => {
      const wrapper = renderComponent({ comment, loading });
      assert.equal(getToggleButton(wrapper).prop('title'), expectedTitle);
    });
  });

  ['comment-textless-close-button', 'comment-close-button'].forEach(
    closeButtonTestId => {
      it('closes popover when clicking close buttons', () => {
        const wrapper = renderComponent();

        togglePopover(wrapper);
        assert.isTrue(commentPopoverExists(wrapper));

        wrapper
          .find(`button[data-testid="${closeButtonTestId}"]`)
          .simulate('click');
        assert.isFalse(commentPopoverExists(wrapper));
      });
    },
  );

  context('when clicking internal popover submit button', () => {
    const clickSubmit = wrapper =>
      wrapper
        .find('button[data-testid="comment-submit-button"]')
        .simulate('click');

    it('submits grade', async () => {
      const onSubmit = sinon.stub();
      const wrapper = renderComponent({ onSubmit });

      togglePopover(wrapper);

      clickSubmit(wrapper);
      assert.called(onSubmit);
    });

    it('closes popover after successfully submitting', () => {
      const onSubmit = sinon.stub().returns(true);
      const wrapper = renderComponent({ onSubmit });

      togglePopover(wrapper);

      clickSubmit(wrapper);
      assert.isFalse(commentPopoverExists(wrapper));
    });
  });

  it('updates comment on textarea input', async () => {
    const onInput = sinon.stub();
    const wrapper = renderComponent({ onInput });
    togglePopover(wrapper);

    wrapper.find('textarea').simulate('input');

    assert.called(onInput);
  });

  it(
    'should pass a11y checks',
    checkAccessibility([
      {
        name: 'Popover is closed',
        content: () => renderComponent(),
      },
      {
        name: 'Popover is open',
        content: () => {
          const wrapper = renderComponent();
          togglePopover(wrapper);

          return wrapper;
        },
      },
    ]),
  );
});
