import { freePort5000 } from './free-port';

export default async function globalTeardown() {
  freePort5000();
}
