import _ from 'lodash';
import CanvasApi from './canvas_api';

class BlankState {}

const defaultState = {
  pickerOpen: false,
  selectedUrl: null,
}

export default class Store {
  constructor(subscribers = [], state = defaultState) {
    this.subscribers = subscribers;
    this.canvasApi = new CanvasApi()
    this.eventTypes = eventTypes;
  }

  triggerUpdate(eventType) {
    _.each(this.subscribers, sub => sub.handleUpdate(this.state, eventType));
  }

  setState(state, eventType) {
    this.state = state;
    this.triggerUpdate(eventType)
  }

  getState() {
    return this.state;
  }

  subscribe(subscriber) {
    this.subscribers.push(subscriber);
  }

  unsubscribe(subcriber) {
    _.remove(this.subscribers, s => s === subscriber );
  }
}