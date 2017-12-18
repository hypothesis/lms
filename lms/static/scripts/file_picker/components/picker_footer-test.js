import PickerFooter from './picker_footer';
import Store from '../store';

describe('picker footer', () => {
  it('#render should render the cancel and submit buttons', () => {
    const store = new Store();
    const pickerFooter = new PickerFooter(store);
    assert.include(pickerFooter.render(), 'picker-cancel');
    assert.include(pickerFooter.render(), 'picker-submit');
  });
});