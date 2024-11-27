import { mount } from '@hypothesis/frontend-testing';
import { render } from 'preact';

import { useUniqueId, useDocumentTitle } from '../hooks';

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
