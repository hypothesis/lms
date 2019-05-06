import Component from './component';

export default class PickerHeaderTable extends Component {
  render() {
    return this.r`
      <thead>
        <tr>
          <th scope="col">
            <button class="is-active">
              <span>Name</span>
              <i class="material-icons" aria-label="filter down">arrow_downward</i>
            </button>
          </th>
          <th scope="col">
            <button>
              <span>Last modified</span>
            </button>
          </th>
        </tr>
      </thead>
    `;
  }
}
