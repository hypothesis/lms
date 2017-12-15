import Store from './store';
import FilePicker from './components/file_picker';
const store = new Store();

function pickerCallback(fileId) {
  document.getElementById('url').value = `?canvas_file=true&file_id=${fileId}`;
  document.getElementById('content-item-submit').click();
}

new FilePicker(
  store,
  {
    mountId: '#file-picker',
    courseId: window.DEFAULT_SETTINGS.courseId,
    pickerCallback
  }
).render();