import { createContext } from 'preact';
import type { Context, FunctionComponent } from 'preact';
import { useContext, useMemo } from 'preact/hooks';

export { ClientRPC } from './client-rpc';
export { ContentInfoFetcher } from './content-info-fetcher';
export { GradingService } from './grading';
export { VitalSourceService } from './vitalsource';

/** Type that any class can be assigned to. */
export type Constructor = new (...args: any[]) => unknown;

/**
 * Directory of available services.
 *
 * The directory is a map of service class to instance. The instances don't
 * have to be instances of the exact class, but they must have the same interface.
 */
export type ServiceMap = Map<Constructor, unknown>;

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
 */
export const Services: Context<ServiceMap> = createContext(new Map());

/**
 * Hook that looks up a service.
 *
 * There must be a `Services.Provider` component higher up the component tree
 * which provides the service. This hook throws if the service is not available.
 *
 * @param class_ - The service class. This is used as a key to look up the instance.
 * @return - Registered instance which implements `class_`'s interface
 */
export function useService<Class extends Constructor>(
  class_: Class,
): InstanceType<Class> {
  const serviceMap = useContext(Services);
  const service = serviceMap.get(class_);
  if (!service) {
    throw new Error(`Service "${class_.name}" is not registered`);
  }
  return service as InstanceType<Class>;
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
 * @param getServices -
 *   Callback that returns an array of `[ServiceClass, instance]` tuples, called
 *   when the component is first rendered.
 */
export function withServices(
  Component: FunctionComponent,
  getServices: () => [class_: Constructor, instance: any][],
) {
  const ComponentWrapper = (props: object) => {
    const services = useMemo(() => new Map(getServices()), []);
    return (
      <Services.Provider value={services}>
        <Component {...props} />
      </Services.Provider>
    );
  };
  return ComponentWrapper;
}
