import $ from 'jquery/dist/jquery.min.js';
import _ from 'lodash';
import Component from './component';
import PickerTableHeader from './picker_table_header';
import PickerTableRow from './picker_table_row';
import PickerFooter from './picker_footer';
import { Constants } from '../canvas_api';

export default class FilePicker extends Component{
  initializeComponent() {
    this.store.subscribe(this);
  }

  setupEventListeners() {
    $('#picker-button').on('click', () => {
      const state = this.store.getState();
      this.store.setState(
        { ...state, pickerOpen: true },
        this.store.eventTypes.PICKER_OPENED
      );
    });
  }

  handleUpdate(state, eventType) {
    this.setupEventListeners();
    if (eventType !== this.store.eventTypes.DOCUMENT_RENDERED) {
      this.render();
    }
    if (eventType === this.store.eventTypes.PICKER_OPENED) {
      this.store.canvasApi.proxy(
        `courses/${this.props.courseId}/files`,
        Constants.GET_ALL
      ).then((res) => {
        const currentState = this.store.getState()
        this.store.setState({
            ...currentState,
            files: JSON.parse(res.text),
          },
          this.store.eventTypes.FILES_LOADED
        )
      });
    }
  }

  render() {
    const state = this.store.getState();
    let output;
    if(state.pickerOpen) {
      output = this.r`
        <div class="file-picker-modal">
          <main class="picker-content">
            <div class="scroll-container">
              <table class="list-view" role="listbox">
                ${new PickerTableHeader(this.store)}
                <tbody>
                  ${_.map(state.files, (file) => new PickerTableRow(this.store, { file }))}
                </tbody>
              </table>
            </div>
            ${new PickerFooter(
              this.store,
              { pickerCallback: this.props.pickerCallback }
            )}
          </main>
        </div>
        <div class="file-picker-overlay" />
      `;
    } else {
      output = this.r`
        <button
          class="btn btn--gray"
          id="picker-button"
        >
          Use Canvas File
        </button>
      `;
    }
    $(this.props.mountId).html(output)
    this.store.triggerUpdate(this.store.eventTypes.DOCUMENT_RENDERED)
  }
}
