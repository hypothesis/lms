import $ from 'jquery/dist/jquery.min.js';
import Component from './component';

export default class PickerHeaderTable extends Component {

  initializeComponent() {
    this.store.subscribe(this);
  }

  handleUpdate() {
    // Handle the submit and cancel functionality.
    $('#picker-cancel').off('click');
    $('#picker-cancel').on('click', () => {
      this.store.setState(
        {
          ...this.store.getState(),
          pickerOpen: false,
        },
        this.store.eventTypes.PICKER_CLOSED
      );
    });
    $('#picker-submit').off('click');
    $('#picker-submit').on('click', () => {
      this.props.pickerCallback(
        this.store.getState().selectedFileId
      );
      this.store.setState(
        {
          ...this.store.getState(),
          pickerOpen: false,
        },
        this.store.eventTypes.FILE_SUBMITTED
      );
    });
  }

  render() {
    return this.r`
      <footer>
        <button id="picker-cancel" class="btn btn--gray">Cancel</button>
        <button id="picker-submit" class="btn btn--red">Submit</button>
      </footer>
    `;
  }
}