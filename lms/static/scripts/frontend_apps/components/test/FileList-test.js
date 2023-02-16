import { mount } from 'enzyme';

import FileList, { $imports } from '../FileList';
import { checkAccessibility } from '../../../test-util/accessibility';
import mockImportedComponents from '../../../test-util/mock-imported-components';

describe('FileList', () => {
  const testFiles = [
    {
      id: 123,
      display_name: 'Test.pdf',
      updated_at: '2019-05-09T17:45:21+00:00Z',
    },
  ];

  const renderFileList = (props = {}) =>
    mount(<FileList files={testFiles} {...props} />);

  const renderFilesListNoFiles = (props = {}) =>
    mount(<FileList files={[]} {...props} />);

  beforeEach(() => {
    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('renders a table with "Name" and "Last modified" columns', () => {
    const wrapper = renderFileList();
    const columns = wrapper.find('thead');
    assert.include(columns.text(), 'Name');
    assert.include(columns.text(), 'Last modified');
  });

  it('renders files with an icon, file name and date', () => {
    const wrapper = renderFileList();
    const formattedDate = new Date(testFiles[0]).toLocaleDateString();
    const dataRow = wrapper.find('tbody tr').at(0);
    assert.isTrue(dataRow.find('FilePdfFilledIcon').exists());
    assert.equal(dataRow.find('td').at(0).text(), testFiles[0].display_name);
    assert.equal(dataRow.find('td').at(1).text(), formattedDate);
  });

  it('renders a explanatory message when there are no files', () => {
    const wrapper = renderFilesListNoFiles({
      isLoading: false,
      noFilesMessage: <div className="FileList__no-files-message" />,
    });
    assert.isTrue(wrapper.exists('.FileList__no-files-message'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility([
      {
        name: 'files loaded',
        content: () => renderFileList({ isLoading: false }),
      },
      {
        name: 'loading',
        content: () => renderFileList({ isLoading: true }),
      },
    ])
  );
});
