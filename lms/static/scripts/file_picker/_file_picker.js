import Store from './store';
import FilePicker from './components/file_picker';
const store = new Store();

new FilePicker(store, { mountId: '#file-picker' }).render();