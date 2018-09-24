import PickerTableRow from './picker_table_row';
import Store from '../store';
describe('picker table row', () => {
  it('#render renders the filename update_at attrs', () => {
    const store = new Store();
    const file = {
      filename: 'Test',
      updated_at: '11/11/11',
      id: '1',
    };
    const pickerTableRow = new PickerTableRow(store, { file });
    const output = pickerTableRow.render();
    assert.include(output, 'Test'),
    assert.include(output, '11/11/11');
  });
});