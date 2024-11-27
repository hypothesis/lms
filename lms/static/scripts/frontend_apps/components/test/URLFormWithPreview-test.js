import { mount } from '@hypothesis/frontend-testing';
import { createRef } from 'preact';

import URLFormWithPreview from '../URLFormWithPreview';

describe('URLFormWithPreview', () => {
  const renderComponent = (props = {}) =>
    mount(
      <URLFormWithPreview
        label="Default label"
        onURLChange={sinon.stub()}
        onInput={sinon.stub()}
        inputRef={createRef()}
        {...props}
      />,
    );

  it('pre-fills input with `defaultURL` prop value', () => {
    const wrapper = renderComponent({
      defaultURL: 'https://arxiv.org/pdf/1234.pdf',
    });
    assert.equal(
      wrapper.find('input').getDOMNode().value,
      'https://arxiv.org/pdf/1234.pdf',
    );
  });

  it('displays children if provided', () => {
    const wrapper = renderComponent({
      children: <span data-testid="form-children">Foo</span>,
    });
    const childrenComponent = wrapper.find('[data-testid="form-children"]');

    assert.isTrue(childrenComponent.exists());
    assert.equal(childrenComponent.text(), 'Foo');
  });

  it('displays error if provided', () => {
    const error = 'Something went wrong';
    const wrapper = renderComponent({ error });
    const errorComponent = wrapper.find('UIMessage[status="error"]');

    assert.isTrue(errorComponent.exists());
    assert.equal(errorComponent.text(), error);
  });

  it('displays label as provided', () => {
    const label = 'Introduce some URL';
    const wrapper = renderComponent({ label });
    const labelComponent = wrapper.find('label');

    assert.isTrue(labelComponent.exists());
    assert.equal(labelComponent.text(), label);
  });

  [
    { orientation: 'square', expectedClass: 'h-[200px]' },
    { orientation: 'landscape', expectedClass: 'h-[120px]' },
  ].forEach(({ orientation, expectedClass }) => {
    it(`has proper thumbnail container classes for "${orientation}" orientation`, () => {
      const wrapper = renderComponent({
        thumbnail: { orientation },
      });
      const thumbnailContainer = wrapper.find('Thumbnail').parent();

      assert.include(thumbnailContainer.prop('className'), expectedClass);
    });
  });

  [
    { orientation: 'square', expectedRatio: '1/1' },
    { orientation: 'landscape', expectedRatio: '16/9' },
  ].forEach(({ orientation, expectedRatio }) => {
    it(`has proper thumbnail ratio for "${orientation}" orientation`, () => {
      const wrapper = renderComponent({
        thumbnail: { orientation },
      });
      const thumbnail = wrapper.find('Thumbnail');

      assert.equal(thumbnail.prop('ratio'), expectedRatio);
    });
  });

  it('does not render thumbnail img if not provided', () => {
    const wrapper = renderComponent();
    const thumbnail = wrapper.find('Thumbnail');

    assert.isFalse(thumbnail.find('img').exists());
  });

  it('renders thumbnail img if provided', () => {
    const wrapper = renderComponent({
      thumbnail: {
        image: 'https://placekitten.com/400/400',
        alt: 'Placeholder kitten',
      },
    });
    const thumbnail = wrapper.find('Thumbnail');
    const img = thumbnail.find('img');

    assert.isTrue(img.exists());
    assert.equal(img.prop('src'), 'https://placekitten.com/400/400');
    assert.equal(img.prop('alt'), 'Placeholder kitten');
  });

  context('entering, changing and submitting URL', () => {
    it('invokes `onURLChange` when the value of the url input changes', () => {
      const onURLChange = sinon.stub();
      const wrapper = renderComponent({ onURLChange });
      const input = wrapper.find('input');

      input.getDOMNode().value = 'https://example.com';
      input.simulate('change');

      assert.calledWith(onURLChange, 'https://example.com');
    });

    it('invokes `onURLChange` when Enter key is pressed on url input', () => {
      const onURLChange = sinon.stub();
      const wrapper = renderComponent({ onURLChange });
      const inputDomNode = wrapper.find('Input').find('input').getDOMNode();

      const keyEvent = new Event('keydown');
      keyEvent.key = 'Enter';

      inputDomNode.value = 'https://example.com';
      inputDomNode.dispatchEvent(keyEvent);

      assert.calledWith(onURLChange, 'https://example.com');
    });

    it('invokes `onURLChange` when confirm button is clicked', () => {
      const onURLChange = sinon.stub();
      const wrapper = renderComponent({ onURLChange });
      const input = wrapper.find('input');
      const button = wrapper.find('IconButton').find('button');

      input.getDOMNode().value = 'https://example.com';
      button.simulate('click');

      assert.calledWith(onURLChange, 'https://example.com');
    });
  });

  it('invokes `onInput` when URL input content is modified', () => {
    const onInput = sinon.stub();
    const wrapper = renderComponent({ onInput });

    wrapper.find('input').simulate('input');

    assert.called(onInput);
  });
});
