import { mount } from '@hypothesis/frontend-testing';

import TableOfContentsPicker from '../TableOfContentsPicker';

describe('TableOfContentsPicker', () => {
  const tocData = [
    {
      title: 'Chapter One',
      level: 1,
      page: '10',
    },
    {
      title: 'Chapter Two',
      level: 1,
      page: '20',
    },
    {
      title: 'Chapter Two - Part 1',
      level: 2,
      page: '20',
    },
  ];
  const noop = () => {};
  const renderTableOfContentsPicker = (props = {}) =>
    mount(
      <TableOfContentsPicker
        entries={tocData}
        selectedEntry={null}
        onSelectEntry={noop}
        onConfirmEntry={noop}
        {...props}
      />,
    );

  describe('initial focus', () => {
    it('focuses the URL text input element', () => {
      const beforeFocused = document.activeElement;

      const wrapper = mount(
        <TableOfContentsPicker
          chapters={tocData}
          selectedEntry={null}
          onSelectEntry={noop}
          onConfirmEntry={noop}
        />,
        {
          connected: true,
        },
      );

      const focused = document.activeElement;
      const table = wrapper.find('table[data-testid="toc-table"]').getDOMNode();

      assert.notEqual(beforeFocused, focused);
      assert.equal(focused, table);
    });
  });

  it('renders entry titles', () => {
    const toc = renderTableOfContentsPicker();
    const rows = toc.find('tbody tr');
    assert.equal(rows.length, tocData.length);
    assert.equal(rows.at(0).find('td').at(0).text(), tocData[0].title);
    assert.equal(rows.at(0).find('td').at(1).text(), tocData[0].page);

    const tocLevels = [
      rows.at(0).find('[data-testid="toc-indent"]').prop('data-level'),
      rows.at(1).find('[data-testid="toc-indent"]').prop('data-level'),
      rows.at(2).find('[data-testid="toc-indent"]').prop('data-level'),
    ];
    assert.deepEqual(tocLevels, [0, 0, 1]);
  });

  [true, false].forEach(isLoading => {
    it('shows loading indicator in table if chapters are being fetched', () => {
      const toc = renderTableOfContentsPicker({ isLoading });
      assert.equal(toc.find('DataTable').prop('loading'), isLoading);
    });
  });

  it('calls `onSelectEntry` callback when a chapter is selected', () => {
    const onSelectEntry = sinon.stub();
    const toc = renderTableOfContentsPicker({ onSelectEntry });

    toc.find('DataTable').prop('onSelectRow')(tocData[0]);

    assert.calledWith(onSelectEntry, tocData[0]);
  });

  it('calls `onConfirmEntry` callback when a chapter is double-clicked', () => {
    const onConfirmEntry = sinon.stub();
    const toc = renderTableOfContentsPicker({ onConfirmEntry });

    toc.find('DataTable').prop('onConfirmRow')(tocData[0]);

    assert.calledWith(onConfirmEntry, tocData[0]);
  });
});
