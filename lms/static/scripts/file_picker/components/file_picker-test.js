import FilePicker from './file_picker';
import Store from '../store';

describe('file picker', () => {

  it('#handleUpdate should call setupEventListeners', () => {
    const store = new Store();
    const filePicker = new FilePicker(store, {});
    filePicker.setupEventListeners = sinon.stub();
    filePicker.handleUpdate({}, 'test');
    assert.called(filePicker.setupEventListeners);
  });

  it('#render calls trigger update on the store', () => {
    const store = new Store();
    const filePicker = new FilePicker(store, {});
    store.triggerUpdate = sinon.stub();
    filePicker.render();
    assert.calledWith(
      store.triggerUpdate,
      store.eventTypes.DOCUMENT_RENDERED
    );
  });

  it('only renders the picker if the pickerOpen state is true', () => {
    const store = new Store();
    const filePicker = new FilePicker(store, {});
    store.unsubscribe(filePicker); // hack to avoid api calls
    const output = filePicker.render();
    assert.include(output, 'picker-button')
    store.setState(
      {
        ...store.getState(),
        pickerOpen: true
      },
      store.eventTypes.PICKER_OPENED
    );
    const secondOutput = filePicker.render();
    assert.include(secondOutput, '<main')
  });
});