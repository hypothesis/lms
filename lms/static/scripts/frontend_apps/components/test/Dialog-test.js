import { mount } from 'enzyme';
import { createElement, createRef } from 'preact';

import Dialog from '../Dialog';
import { checkAccessibility } from '../../../test-util/accessibility';

describe('Dialog', () => {
  it('renders content', () => {
    const wrapper = mount(
      <Dialog>
        <span>content</span>
      </Dialog>
    );
    assert.isTrue(wrapper.contains(<span>content</span>));
  });

  it('adds `contentClass` value to class list', () => {
    const wrapper = mount(
      <Dialog contentClass="foo">
        <span>content</span>
      </Dialog>
    );
    assert.isTrue(wrapper.find('.Dialog__content').hasClass('foo'));
  });

  it('renders buttons', () => {
    const wrapper = mount(
      <Dialog
        buttons={[
          <button key="foo" name="foo" />,
          <button key="bar" name="bar" />,
        ]}
      />
    );
    assert.isTrue(wrapper.contains(<button key="foo" name="foo" />));
    assert.isTrue(wrapper.contains(<button key="bar" name="bar" />));
  });

  it('renders the title', () => {
    const wrapper = mount(<Dialog title="Test dialog" />);
    const header = wrapper.find('h1');
    assert.equal(header.text().indexOf('Test dialog'), 0);
  });

  it('closes when Escape key is pressed', () => {
    const onCancel = sinon.stub();
    const container = document.createElement('div');
    document.body.appendChild(container);
    mount(<Dialog title="Test dialog" onCancel={onCancel} />, {
      attachTo: container,
    });

    const event = new Event('keydown');
    event.key = 'Escape';
    document.body.dispatchEvent(event);
    assert.called(onCancel);
    container.remove();
  });

  it('closes when close button is clicked', () => {
    const onCancel = sinon.stub();
    const wrapper = mount(<Dialog title="Test dialog" onCancel={onCancel} />);

    wrapper.find('.Dialog__cancel-btn').simulate('click');

    assert.called(onCancel);
  });

  it('focuses the `initialFocus` ref if set', () => {
    const container = document.createElement('div');
    document.body.appendChild(container);

    const inputRef = createRef();
    mount(
      <Dialog initialFocus={inputRef}>
        <input ref={inputRef} />
      </Dialog>,
      { attachTo: container }
    );
    assert.equal(document.activeElement, inputRef.current);

    container.remove();
  });

  it('focuses the root element of the dialog if no `initialFocus` is set', () => {
    const container = document.createElement('div');
    document.body.appendChild(container);

    const wrapper = mount(
      <Dialog>
        <div>Test</div>
      </Dialog>,
      { attachTo: container }
    );

    assert.equal(
      document.activeElement,
      wrapper.find('[role="dialog"]').getDOMNode()
    );

    container.remove();
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      // eslint-disable-next-line react/display-name
      content: () => (
        <Dialog title="Test dialog">
          <div>test</div>
        </Dialog>
      ),
    })
  );
});
