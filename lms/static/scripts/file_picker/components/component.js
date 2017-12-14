import _ from 'lodash';

export default class Component {
  constructor(store, props) {
    this.store = store;
    this.props = props;
    this.initializeComponent();
  }

  initializeComponent() {}

  render() {};

  r(parts, ...components) {
    return _.chain(parts)
      .map((part, index) => {
        const comp = components[index];
        // handle rendering of strings and other primitive values
        if(comp && typeof comp !== 'object') {
          return `${part}${comp}`;
        }
        let output = _.chain([comp])
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