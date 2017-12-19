import _ from 'lodash';
import CanvasApi from './canvas_api';

const defaultState = {
  pickerOpen: false,
  selectedFileId: null,
  files: [],
}

const eventTypes = {
  DOCUMENT_RENDERED: 'DOCUMENT_RENDERED',
  FILES_LOADED: 'FILES_LOADED',
  PICKER_OPENED: 'PICKER_OPENED',
  PICKER_CLOSED: 'PICKER_CLOSED',
  FILE_SELECTED: 'FILE_SELECTED',
  FILE_SUBMITED: 'FILE_SUBMITTED',
}

// Store handles the application state and implements a basic observer pattern.
// Subscribers are notified any time an update is triggered via the triggerUpdate function, the
// subscriber will recieve the current state and a message describing the update.
export default class Store {
  constructor(subscribers = [], state = defaultState) {
    this.subscribers = subscribers;
    this.canvasApi = new CanvasApi();
    this.eventTypes = eventTypes;
    this.state = state;
  }

  // Notify all subscribers of an update
  triggerUpdate(eventType) {
    _.each(this.subscribers, sub => sub.handleUpdate(this.state, eventType));
  }

  // Replaces existing state with new state then triggers and update.
  setState(state, eventType) {
    this.state = state;
    this.triggerUpdate(eventType);
  }

  getState() {
    return this.state;
  }

  subscribe(subscriber) {
    this.subscribers.push(subscriber);
  }

  unsubscribe(subscriber) {
    _.remove(this.subscribers, s => s === subscriber );
  }
}