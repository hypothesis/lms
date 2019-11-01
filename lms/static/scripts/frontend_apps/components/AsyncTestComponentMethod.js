export default function asyncMethod() {
  return new Promise(resolve => {
    resolve('dummy');
  });
}
