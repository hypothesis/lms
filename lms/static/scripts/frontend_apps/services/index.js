import { createContext } from 'preact';
import { useContext, useMemo } from 'preact/hooks';

export { ClientRPC } from './client-rpc';
export { GradingService } from './grading';
export { VitalSourceService } from './vitalsource';

/**
 * Directory of available services.
 *
 * The directory is a map of service class to instance. The instances don't
 * have to be instances of the exact class, but they must have the same interface.
 *
 * @typedef {Map<Function, unknown>} ServiceMap
 */

/**
 * Context object used to make services available to components.
 *
 * A `Services.Provider` component must be rendered at the top of the tree
 * with a directory of available services. Components within the tree can access
 * the service instances using the `useService` hook.
 *
 * @example
 *   const MyApp = (props) => {
 *     const fooService = useService(FooService);
 *     fooService.doSomething();
 *     ...
 *   };
 *
 *   const services = new Map();
 *   services.set(FooService, new FooService(...));
 *   <Services.Provider value={services}>
 *     <MyApp />
 *   </Services.Provider>
 *
 * @type {import('preact').Context<ServiceMap>}
 */
export const Services = createContext(new Map());

/**
 * Hook that looks up a service.
 *
 * There must be a `Services.Provider` component higher up the component tree
 * which provides the service. This hook throws if the service is not available.
 *
 * @template {new (...args: any) => any} Class
 * @param {Class} class_ - The service class. This is used as a key to look up the instance.
 * @return {InstanceType<Class>} - Registered instance which implements `class_`'s interface
 */
export function useService(class_) {
  const serviceMap = useContext(Services);
  const service = serviceMap.get(class_);
  if (!service) {
    throw new Error(`Service "${class_.name}" is not registered`);
  }
  return /** @type {InstanceType<Class>} */ (service);
}

/**
 * Utility that wraps a component that relies on services with a `Services.Provider`.
 *
 * This is mainly useful in tests for such components. In non-test environments,
 * there should generally be a `<Services.Provider>` near the root of the tree.
 *
 * The wrapped component accepts the same props as the original.
 *
 * @example
 *   const WidgetWrapper = withServices(Widget, () => [[APIService, apiService]]);
 *   render(<WidgetWrapper someProp={aValue}/>, container)
 *
 * @param {import('preact').FunctionComponent} Component
 * @param {() => [class_: Function, instance: any][]} getServices -
 *   Callback that returns an array of `[ServiceClass, instance]` tuples, called
 *   when the component is first rendered.
 */
export function withServices(Component, getServices) {
  /** @param {object} props */
  const ComponentWrapper = props => {
    const services = useMemo(() => new Map(getServices()), []);
    return (
      <Services.Provider value={services}>
        <Component {...props} />
      </Services.Provider>
    );
  };
  return ComponentWrapper;
}
