import { mount } from 'enzyme';

import VitalSourceBookViewer from '../VitalSourceBookViewer';

describe('VitalSourceBookViewer', () => {
  let container;
  let launchForm;
  let wrappers;

  const createComponent = ({ launchURL, launchParams }) => {
    const beforeSubmit = form => {
      sinon.stub(form, 'submit');
      launchForm = form;
    };
    const wrapper = mount(
      <VitalSourceBookViewer
        launchUrl={launchURL}
        launchParams={launchParams}
        willSubmitLaunchForm={beforeSubmit}
      />,

      // The `VitalSourceBookViewer` must be rendered into a connected element
      // for the iframe's document to be created.
      { attachTo: container }
    );
    wrappers.push(wrapper);
    return wrapper;
  };

  beforeEach(() => {
    wrappers = [];
    launchForm = null;
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    wrappers.forEach(w => w.unmount());
    container.remove();
  });

  it('renders the launch URL in an iframe if no form parameters are provided', () => {
    const launchURL =
      'https://hypothesis.vitalsource.com/books/abc/cfi/chapter1';
    const wrapper = createComponent({ launchURL });
    const frame = wrapper.find('iframe');
    assert.isTrue(wrapper.exists());
    assert.equal(frame.props().src, launchURL);
  });

  it('creates and submits a form if form parameters are provided', () => {
    const launchParams = {
      roles: 'Learner',
      context_id: 'testcourse',
      location: 'chapter-1',
    };
    const launchURL = 'https://hypothesis.vitalsource.com/launch';
    const onSubmit = sinon.stub();

    createComponent({
      launchURL,
      launchParams,
      onSubmit,
    });

    assert.ok(launchForm);
    assert.calledOnce(launchForm.submit);
    assert.equal(launchForm.tagName, 'FORM');
    assert.equal(launchForm.method, 'post');
    assert.equal(launchForm.action, launchURL);

    const fields = Array.from(launchForm.elements).reduce((obj, el) => {
      obj[el.name] = el.value;
      return obj;
    }, {});
    assert.deepEqual(fields, launchParams);
  });
});
