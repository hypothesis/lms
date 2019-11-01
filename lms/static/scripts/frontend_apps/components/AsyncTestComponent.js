import { createElement } from 'preact';
import propTypes from 'prop-types';
import { useState, useEffect } from 'preact/hooks';
import asyncMethod from './AsyncTestComponentMethod';

export default function AsyncTestComponent({ firstValue, secondValue }) {
  const [stateValue, setStateValue] = useState('');

  useEffect(() => {
    const asyncSetValues = async () => {
      setStateValue('initial_value');
      try {
        if (firstValue) {
          const asyncValue = await asyncMethod();
          setStateValue(firstValue + asyncValue);
        }
      } catch (e) {
        setStateValue(e.name);
      }

      if (secondValue) {
        setStateValue(secondValue);
      }
    };

    asyncSetValues();
  }, [firstValue, secondValue]);

  return <div>{stateValue}</div>;
}

AsyncTestComponent.propTypes = {
  firstValue: propTypes.string,
  secondValue: propTypes.string,
};
