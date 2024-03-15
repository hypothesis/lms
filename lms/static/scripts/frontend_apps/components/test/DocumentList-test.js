import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import DocumentList, { $imports } from '../DocumentList';

describe('DocumentList', () => {
  const testDocuments = [
    {
      id: 123,
      display_name: 'Test.pdf',
      updated_at: '2019-05-09T17:45:21+00:00Z',
      type: 'File',
      mime_type: 'application/pdf',
    },
  ];

  const renderDocumentList = (props = {}) =>
    mount(
      <DocumentList title="File list" documents={testDocuments} {...props} />,
    );

  const renderDocumentListNoDocuments = (props = {}) =>
    mount(<DocumentList title="File list" documents={[]} {...props} />);

  beforeEach(() => {
    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('renders a table with "Name" and "Last modified" columns', () => {
    const wrapper = renderDocumentList();
    const columns = wrapper.find('thead');
    assert.include(columns.text(), 'Name');
    assert.include(columns.text(), 'Last modified');
  });

  [
    // Folder
    { type: 'Folder', icon: 'FolderIcon' },

    // Files with known mime type
    { type: 'File', mime_type: 'application/pdf', icon: 'FilePdfFilledIcon' },
    { type: 'File', mime_type: 'text/html', icon: 'FileGenericIcon' },
    { type: 'File', mime_type: 'video', icon: 'PreviewIcon' },

    // File with unknown mime type
    { type: 'File', icon: 'FileGenericIcon' },
  ].forEach(({ type, mime_type, icon }) => {
    it('renders documents with an icon, document name and date', () => {
      const wrapper = renderDocumentList({
        documents: [{ ...testDocuments[0], type, mime_type }],
      });
      const formattedDate = new Date(testDocuments[0]).toLocaleDateString();
      const dataRow = wrapper.find('tbody tr').at(0);
      assert.isTrue(dataRow.find(icon).exists());
      assert.equal(
        dataRow.find('td').at(0).text(),
        testDocuments[0].display_name,
      );
      assert.equal(dataRow.find('td').at(1).text(), formattedDate);
    });
  });

  it('renders a explanatory message when there are no documents', () => {
    const wrapper = renderDocumentListNoDocuments({
      isLoading: false,
      noDocumentsMessage: <div data-testid="no-files-message" />,
    });
    assert.isTrue(wrapper.exists('[data-testid="no-files-message"]'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility([
      {
        name: 'documents loaded',
        content: () => renderDocumentList({ isLoading: false }),
      },
      {
        name: 'loading',
        content: () => renderDocumentList({ isLoading: true }),
      },
    ]),
  );
});
