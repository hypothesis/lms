import _ from 'lodash';

// All UI elements extend this class.
// Provides a declarative rendering api and some lifecycle methods.
export default class Component {
  // All the args are optional but recommend at the very least passing in the store.
  constructor(store, props) {
    this.store = store;
    this.props = props;
    this.initializeComponent();
  }

  // A hook to override that gets called upon object construction
  initializeComponent() {}

  // Return an html string from this method. Can be called explicitly or will be
  // called by the `r` method below.
  render() {}

  // A template literal tag that takes a template literal interploted with
  // instances of the Component class.
  // See https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals
  // for more information on tagged template literals
  r(parts, ...components) {
    return _.chain(parts)
      .map((part, index) => {
        const comp = components[index];
        // handle rendering of strings and other primitive values
        if (comp && typeof comp !== 'object') {
          return `${part}${comp}`;
        }
        const output = _.chain([comp])
          .flatten()
          .compact()
          .map(value => value.render())
          .join('')
          .value();
        return `${part}${output}`;
      })
      .join('')
      .value();
  }
}