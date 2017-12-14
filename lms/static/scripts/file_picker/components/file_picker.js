import $ from 'jquery/dist/jquery.min.js';
import _ from 'lodash';
import Component from './component';
import PickerTableHeader from './picker_table_header';
import PickerTableRow from './picker_table_row';
import PickerFooter from './picker_footer';

const MOCK_FILES = [
  {fileName: 'file1.pdf', lastUpdatedAt: '11/11/11'},
  {fileName: 'file1.pdf', lastUpdatedAt: '11/11/11'},
  {fileName: 'file1.pdf', lastUpdatedAt: '11/11/11'},
  {fileName: 'file1.pdf', lastUpdatedAt: '11/11/11'}
];

export default class FilePicker extends Component{
  initializeComponent() {
    this.store.subscribe(this)
    this.store.canvasApi.proxy('')
  }

  handleUpdate(state, eventType) {
    this.render();
  }

  render() {
    const output = this.r`
      <main class="picker-content">
        <div class="scroll-container">
          <table class="list-view" role="listbox">
            ${new PickerTableHeader(this.store)}
            <tbody>
              ${_.map(MOCK_FILES, (file) => new PickerTableRow(this.store, { file }))}
            </tbody>
          </table>
        </div>
        ${new PickerFooter(this.store)}
      </main>
    `;
    $(this.props.mountId).html(output)
    this.store.triggerUpdate(this.store.eventTypes.DOCUMENT_RENDERED)
  }
}