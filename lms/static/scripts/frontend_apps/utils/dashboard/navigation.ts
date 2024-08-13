import { urlPath } from '../api';

export function assignmentURL(id: number) {
  return urlPath`/assignments/${String(id)}/`;
}

export function courseURL(id: number | string) {
  return urlPath`/courses/${String(id)}/`;
}
