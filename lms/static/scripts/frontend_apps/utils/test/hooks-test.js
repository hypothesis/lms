import { mount } from 'enzyme';
import { render } from 'preact';
import { useRef } from 'preact/hooks';

import { useUniqueId, useDocumentTitle, useElementIsTruncated } from '../hooks';

describe('useUniqueId', () => {
  it('generates unique ids each time useUniqueId is called', () => {
    let id1;
    let id2;

    function Widget() {
      id1 = useUniqueId('prefix:');
      id2 = useUniqueId('prefix:');
      return null;
    }
    render(<Widget />, document.createElement('div'));

    assert.typeOf(id1, 'string');
    assert.typeOf(id2, 'string');
    assert.isTrue(id1.startsWith('prefix:'));
    assert.isTrue(id2.startsWith('prefix:'));
    assert.notEqual(id1, id2);
  });
});

describe('useDocumentTitle', () => {
  let initialDocTitle;

  beforeEach(() => {
    initialDocTitle = document.title;
  });

  afterEach(() => {
    // Reset document title back to its initial state to avoid affecting other
    // tests
    document.title = initialDocTitle;
  });

  function FakeComponent({ documentTitle }) {
    useDocumentTitle(documentTitle);
    return <div />;
  }

  ['foo bar', 'something', 'hello world'].forEach(documentTitle => {
    it('updates document title', () => {
      mount(<FakeComponent documentTitle={documentTitle} />);
      assert.equal(document.title, `${documentTitle} - Hypothesis`);
    });
  });
});

describe('useElementIsTruncated', () => {
  let wrappers;
  let containers;

  function FakeComponent({ children, setRef }) {
    const contentRef = useRef(null);
    const isTruncated = useElementIsTruncated(contentRef);

    return (
      <>
        <div className="w-32 truncate" ref={setRef ? contentRef : undefined}>
          {children}
        </div>
        <div data-testid="is-truncated">{isTruncated ? 'yes' : 'no'}</div>
      </>
    );
  }

  beforeEach(() => {
    wrappers = [];
    containers = [];
  });

  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount());
    containers.forEach(container => container.remove());
  });

  function createComponent({ content, setRef = true }) {
    const container = document.createElement('div');
    document.body.appendChild(container);

    const wrapper = mount(
      <FakeComponent setRef={setRef}>{content}</FakeComponent>,
      {
        attachTo: container,
      },
    );

    containers.push(container);
    wrappers.push(wrapper);

    return wrapper;
  }

  [
    { content: 'short', isTruncated: false },
    { content: 'long'.repeat(100), isTruncated: true },
  ].forEach(({ content, isTruncated }) => {
    it('detects that too long content gets truncated', () => {
      const wrapper = createComponent({ content });
      assert.equal(
        wrapper.find('[data-testid="is-truncated"]').text(),
        isTruncated ? 'yes' : 'no',
      );
    });
  });

  it('does not detected truncated text when ref is not set', () => {
    const wrapper = createComponent({
      content: 'long'.repeat(100),
      setRef: false,
    });
    assert.equal(wrapper.find('[data-testid="is-truncated"]').text(), 'no');
  });
});
