import Component from './component';

export default class PickerFooter extends Component {

  initializeComponent() {
    this.store.subscribe(this)
  }

  handleUpdate(state, eventType) {
    console.log('I got updated too');
  }

  render() {
    return this.r`
      <tr tabindex="0">
        <th scope="row">${this.props.file.fileName}</th>
        <td>${this.props.file.lastUpdatedAt}</td>
      </tr>
    `;
  }
}
