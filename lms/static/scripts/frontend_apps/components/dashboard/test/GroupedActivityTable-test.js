import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import sinon from 'sinon';

import GroupedActivityTable from '../GroupedActivityTable';

describe('GroupedActivityTable', () => {
  const rows = [
    { display_name: 'b', checkpoint_annotations: 8, due_date_annotations: 1 },
    { display_name: 'a', checkpoint_annotations: 3, due_date_annotations: 9 },
    { display_name: 'c', checkpoint_annotations: 5, due_date_annotations: 5 },
  ];
  const groupedColumns = [
    { field: 'display_name', label: 'Student' },
    {
      field: 'checkpoint_annotations',
      label: 'Annotations',
      group: 'Checkpoint',
      initialOrderDirection: 'descending',
    },
    {
      field: 'due_date_annotations',
      label: 'Annotations',
      group: 'Due Date',
      initialOrderDirection: 'descending',
    },
  ];

  let wrappers;

  beforeEach(() => {
    wrappers = [];
  });

  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount());
  });

  function createComponent(props = {}) {
    const wrapper = mount(
      <GroupedActivityTable
        title="Students"
        rows={rows}
        columns={groupedColumns}
        defaultOrderField="display_name"
        renderItem={(row, field) => `${row[field]}`}
        {...props}
      />,
    );
    wrappers.push(wrapper);

    return wrapper;
  }

  /** Text of every cell of the header row at `index`. */
  function headerRow(wrapper, index) {
    return wrapper
      .find('thead tr')
      .at(index)
      .find('th')
      .map(cell => cell.text());
  }

  it('displays a header spanning the columns of each group', () => {
    const wrapper = createComponent();

    // The ungrouped column keeps an empty header, so both rows stay aligned
    assert.deepEqual(headerRow(wrapper, 0), ['', 'Checkpoint', 'Due Date']);
    assert.deepEqual(
      wrapper
        .find('thead tr')
        .at(0)
        .find('th')
        .map(cell => cell.prop('colSpan')),
      [1, 1, 1],
    );
  });

  it('centers the label of a group over its columns', () => {
    const wrapper = createComponent();

    // `TableCell` forces `text-left` on header cells, so the alignment has to
    // live on a wrapper inside the cell
    assert.isTrue(
      wrapper.find('thead tr').at(0).find('th').at(1).exists('div.text-center'),
    );
  });

  it('spans a group over every column which declares it', () => {
    const wrapper = createComponent({
      columns: [
        { field: 'display_name', label: 'Student' },
        {
          field: 'checkpoint_annotations',
          label: 'Annotations',
          group: 'Checkpoint',
        },
        {
          field: 'due_date_annotations',
          label: 'Replies',
          group: 'Checkpoint',
        },
      ],
    });

    assert.deepEqual(headerRow(wrapper, 0), ['', 'Checkpoint']);
    assert.deepEqual(
      wrapper
        .find('thead tr')
        .at(0)
        .find('th')
        .map(cell => cell.prop('colSpan')),
      [1, 2],
    );
  });

  it('does not display a group row when no column declares a group', () => {
    const wrapper = createComponent({
      columns: [
        { field: 'display_name', label: 'Student' },
        { field: 'checkpoint_annotations', label: 'Annotations' },
      ],
    });

    assert.lengthOf(wrapper.find('thead tr'), 1);
    assert.deepEqual(headerRow(wrapper, 0), ['Student', 'Annotations']);
  });

  it('does not stripe the rows, as the other dashboard tables do not', () => {
    const wrapper = createComponent();

    assert.isFalse(wrapper.find('Table').prop('striped'));
  });

  it('sizes the columns which declare a width', () => {
    // `table-fixed` divides the width evenly, which is not enough for a column
    // whose content cannot wrap
    const wrapper = createComponent({
      columns: [
        { field: 'display_name', label: 'Student' },
        {
          field: 'checkpoint_annotations',
          label: 'Annotations',
          width: 'w-40',
        },
      ],
    });

    assert.deepEqual(
      wrapper.find('colgroup col').map(col => col.prop('className')),
      [undefined, 'w-40'],
    );
  });

  it('renders every cell through `renderItem`', () => {
    const renderItem = sinon.stub().returns('cell');
    const wrapper = createComponent({ renderItem });

    assert.equal(
      renderItem.callCount,
      rows.length * groupedColumns.length,
      'every field of every row is rendered',
    );
    assert.calledWith(renderItem, rows[0], 'display_name');
    assert.equal(wrapper.find('tbody td').at(0).text(), 'cell');
  });

  it('orders rows by the default field', () => {
    const wrapper = createComponent();

    assert.deepEqual(
      wrapper.find('tbody tr').map(row => row.find('td').at(0).text()),
      ['a', 'b', 'c'],
    );
  });

  [
    // The first click on a column uses its initial direction
    { clicks: 1, expectedOrder: ['8', '5', '3'] },
    // Clicking it again flips it
    { clicks: 2, expectedOrder: ['3', '5', '8'] },
  ].forEach(({ clicks, expectedOrder }) => {
    it('reorders rows when a column header is clicked', () => {
      const wrapper = createComponent();

      for (let i = 0; i < clicks; i++) {
        wrapper.find('thead tr').at(1).find('button').at(1).simulate('click');
      }

      assert.deepEqual(
        wrapper.find('tbody tr').map(row => row.find('td').at(1).text()),
        expectedOrder,
      );
    });
  });

  it('falls back to the default order when the ordered column goes away', () => {
    const wrapper = createComponent();

    // Order by a column of a group...
    wrapper.find('thead tr').at(1).find('button').at(1).simulate('click');
    assert.deepEqual(
      wrapper.find('tbody tr').map(row => row.find('td').at(1).text()),
      ['8', '5', '3'],
    );

    // ...and then drop it, the way a variant does when the data behind a window
    // goes away. Ordering by a field no column holds would sort nothing and
    // leave no header marked.
    wrapper.setProps({
      columns: [
        { field: 'display_name', label: 'Student' },
        {
          field: 'due_date_annotations',
          label: 'Annotations',
          group: 'Due Date',
        },
      ],
    });

    assert.deepEqual(
      wrapper.find('tbody tr').map(row => row.find('td').at(0).text()),
      ['a', 'b', 'c'],
    );
    assert.equal(
      wrapper.find('thead tr').at(1).find('th').at(0).prop('aria-sort'),
      'ascending',
    );
  });

  it('names a grouped column after its group for assistive technology', () => {
    // `TableCell` scopes every header cell to a single column, so the group
    // cell does not name the columns it spans
    const wrapper = createComponent();
    const labels = wrapper
      .find('thead tr')
      .at(1)
      .find('button')
      .map(button => button.prop('aria-label'));

    assert.deepEqual(labels, [
      undefined,
      'Checkpoint Annotations',
      'Due Date Annotations',
    ]);
  });

  it('marks the ordered column for assistive technology', () => {
    const wrapper = createComponent();

    assert.equal(
      wrapper.find('thead tr').at(1).find('th').at(0).prop('aria-sort'),
      'ascending',
    );
    assert.isUndefined(
      wrapper.find('thead tr').at(1).find('th').at(1).prop('aria-sort'),
    );
  });

  it('shows a spinner instead of the rows while loading', () => {
    const wrapper = createComponent({ loading: true });

    assert.isTrue(wrapper.exists('SpinnerSpokesIcon'));
    assert.lengthOf(wrapper.find('tbody tr'), 1);
  });

  it('shows the empty message when there are no rows', () => {
    const wrapper = createComponent({
      rows: [],
      emptyMessage: 'No students found',
    });

    assert.include(wrapper.find('tbody').text(), 'No students found');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
