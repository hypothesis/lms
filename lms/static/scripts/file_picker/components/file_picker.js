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
    // Remove all the click events the re-add them
    $('#picker-button').off('click');
    $('#picker-button').on('click', () => {
      const state = this.store.getState();
      this.store.setState(
        { ...state, pickerOpen: true },
        this.store.eventTypes.PICKER_OPENED
      );
    });
  }

  // Called by Store when an update is triggered.
  // This method is where you will do things like add and remove event
  // listeners or restore GUI state if needed
  handleUpdate(state, eventType) {
    this.setupEventListeners();
    // We always rerender unless the event is the DOCUMENT RENDERED event
    if (eventType !== this.store.eventTypes.DOCUMENT_RENDERED) {
      const oldContainer = $('.scroll-container')[0] || {};
      const oldScrollTop = oldContainer.scrollTop;
      this.render();
      const newContainer = $('.scroll-container')[0] || {};
      newContainer.scrollTop = oldScrollTop;
    }

    // Load the files from the proxy when the picker is opened.
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
    // Only render the picker if the picker is open
    if(state.pickerOpen) {
      // This can be a little scary if you are not familiar with tagged template
      // literals. https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals
      // Using this is not necessary just more declarative. r simply calls the render
      // method of each component for you, you could very easily call render youself.
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
    } else { // render a button that lets you open the picker if the picker is not open.
      output = this.r`
        <button
          class="btn btn--gray"
          id="picker-button"
        >
          Use Canvas File
        </button>
      `;
    }

    // Find the element on the page and set the inner html to output html
    $(this.props.mountId).html(output)
    // Tell the app we are done rendering so that even listeners can be added.
    this.store.triggerUpdate(this.store.eventTypes.DOCUMENT_RENDERED)
    return output;
  }
}
