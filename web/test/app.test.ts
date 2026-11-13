import { describe, expect, it } from 'vitest';
import { isGuide } from '../src/app';
import { GUIDE_HREF } from '../src/views/guide';

describe('the guide route', () => {
  it('matches the link on the landing page, with or without a slash', () => {
    expect(isGuide(GUIDE_HREF)).toBe(true);
    expect(isGuide('#make-a-snapshot')).toBe(true);
    expect(isGuide('#/make-a-snapshot/')).toBe(true);
  });

  it('leaves the other pages to the router', () => {
    for (const hash of ['', '#/', '#/overview', '#/data', '#/imaginary/make-a-snapshot']) {
      expect(isGuide(hash)).toBe(false);
    }
  });
});
