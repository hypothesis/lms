import Component from './component';
import PickerTableHeader from './picker_table_header';
import $ from 'jquery/dist/jquery.min.js';

export default class FilePicker extends Component{
  initializeComponent() {
    this.store.subscribe(this)
  }

  handleUpdate(state, eventType) {
    console.log('called with ', eventType)
  }

  render() {
    const output = this.r`
      <main class="picker-content">
        <div class="scroll-container">
          <table class="list-view" role="listbox">
            ${new PickerTableHeader(this.store)}
            <tbody>
              <tr tabindex="0">
                <th scope="row">file-name.pdf</th>
                <td>10/24/2017</td>
              </tr>
              <tr tabindex="0">
                <th scope="row">file-name2.pdf</th>
                <td>10/24/2017</td>
              </tr>
              <tr tabindex="0">
                <th scope="row">file-name3.pdf</th>
                <td>10/24/2017</td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer>
          <button class="btn btn--gray">Cancel</button>
          <button class="btn btn--red">Submit</button>
        </footer>
      </main>
    `;
    $(this.props.mountId).html(output)
    this.store.triggerUpdate(this.store.eventTypes.DOCUMENT_RENDERED)
  }
}