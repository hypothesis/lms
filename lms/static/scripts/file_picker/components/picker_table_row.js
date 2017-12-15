import $ from 'jquery/dist/jquery.min.js';
import Component from './component';

export default class PickerFooter extends Component {

  initializeComponent() {
    this.store.subscribe(this);
  }

  handleUpdate(state, eventType) {
    if(eventType === this.store.eventTypes.DOCUMENT_RENDERED) {
      $(`#file-${this.props.file.id}`).on('click', () => {
        this.store.setState(
          {
            ...this.store.getState(),
            selectedFileId: this.props.file.id
          },
          this.store.eventTypes.FILE_SELECTED
        )
      });
    }
  }

  render() {
    const state = this.store.getState()
    let className = '';
    if (this.props.file.id === state.selectedFileId) {
      className = 'class="selected-file"';
    }

    return this.r`
      <tr id="file-${this.props.file.id}" tabindex="0" ${className}>
        <th scope="row">${this.props.file.filename}</th>
        <td>${this.props.file.updated_at}</td>
      </tr>
    `;
  }
}
