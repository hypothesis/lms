import { mount } from 'enzyme';
import { createElement } from 'preact';

import { Services, useService, withServices } from '../index';

class DummyService {}

describe('services/index', () => {
  describe('useService', () => {
    it('returns matching registered service', () => {
      const services = new Map([[DummyService, new DummyService()]]);

      let dataService;
      const Widget = () => {
        dataService = useService(DummyService);
        return null;
      };
      mount(
        <Services.Provider value={services}>
          <Widget />
        </Services.Provider>
      );

      assert.equal(dataService, services.get(DummyService));
    });

    it('throws if service is not registered', () => {
      const TestComponent = () => {
        useService(DummyService);
        return null;
      };

      assert.throws(() => {
        mount(
          <Services.Provider value={new Map()}>
            <TestComponent />
          </Services.Provider>
        );
      }, 'Service "DummyService" is not registered');
    });
  });

  describe('withServices', () => {
    it('renders component within a `Services.Provider` parent', () => {
      let dataService;
      const Widget = () => {
        dataService = useService(DummyService);
        return null;
      };

      const instance = new DummyService();
      const WidgetWrapper = withServices(Widget, () => [
        [DummyService, instance],
      ]);
      mount(<WidgetWrapper />);

      assert.equal(dataService, instance);
    });
  });
});
