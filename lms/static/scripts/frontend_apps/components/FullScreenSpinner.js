import Spinner from './Spinner';

/**
 * A full-screen loading indicator.
 *
 * This consists of a spinner centered in the viewport above a transparent
 * backdrop which dims the content behind it.
 */
export default function FullScreenSpinner() {
  return (
    <div className="FullScreenSpinner__backdrop">
      <Spinner className="FullScreenSpinner__spinner" />
    </div>
  );
}
