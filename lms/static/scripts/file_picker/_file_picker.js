import Store from './store';
import FilePicker from './components/file_picker';
const store = new Store();

// Insert the selected information into the textbox then submit the form.
function pickerCallback(fileId) {
  document.getElementById('url').value = `?canvas_file=true&file_id=${fileId}`;
  document.getElementById('content-item-submit').click();
}

// Initialize the file picker app.
new FilePicker(store, {
  mountId: '#file-picker',
  courseId: window.DEFAULT_SETTINGS.courseId,
  pickerCallback,
}).render();
