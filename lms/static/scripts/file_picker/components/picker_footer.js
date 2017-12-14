import Component from './component';

export default class PickerHeaderTable extends Component {

  initializeComponent() {
    this.store.subscribe(this)
  }

  handleUpdate(state, eventType) {
    console.log('I got updated three');
  }

  render() {
    return this.r`
      <footer>
        <button class="btn btn--gray">Cancel</button>
        <button class="btn btn--red">Submit</button>
      </footer>
    `;
  }
}