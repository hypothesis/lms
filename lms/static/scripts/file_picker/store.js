import _ from 'lodash';
import Api from './api';

class BlankState {}

const eventTypes = {
  DOCUMENT_RENDERED: 'DOCUMENT_RENDERED',
}

export default class Store {
  constructor(subscribers = [], state = new BlankState()) {
    this.subscribers = subscribers;
    this.api = new Api()
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