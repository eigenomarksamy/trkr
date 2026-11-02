import { describe, expect, it } from 'vitest';
import golden from '../../tests/golden/exec/snapshot.json?raw';
import demo from '../public/demo-snapshot.json?raw';
import { parseSnapshot, portfolioNamed, SCHEMA_VERSION, SnapshotError } from '../src/snapshot';

describe('parseSnapshot', () => {
  it('reads the snapshot the CLI writes for the test fixture', () => {
    const snapshot = parseSnapshot(golden);
    expect(snapshot.schema_version).toBe(SCHEMA_VERSION);
    expect(snapshot.portfolio.holdings.map((h) => h.symbol)).toEqual(['AAA.AS', 'BBB']);
    expect(snapshot.portfolio.valuation[0]?.month).toBe('2024-01');
    expect(snapshot.projection).toBeNull();
  });

  it('reads the demo, which is made from local files', () => {
    const snapshot = parseSnapshot(demo);
    expect(snapshot.imaginary.length).toBeGreaterThan(0);
    expect(snapshot.projection?.rows.length).toBeGreaterThan(0);
    expect(Object.values(snapshot.config.sources).every((s) => s === 'local' || s === null)).toBe(true);
  });

  it('says what is wrong with a file that is not a snapshot', () => {
    expect(() => parseSnapshot('not json')).toThrow(/not JSON/);
    expect(() => parseSnapshot('{"a": 1}')).toThrow(/not a trkr snapshot/);
    expect(() => parseSnapshot('{"schema": "trkr-snapshot", "schema_version": 99}')).toThrow(/Update and redeploy/);
    expect(() => parseSnapshot('{"schema": "trkr-snapshot", "schema_version": 0}')).toThrow(/Run trkr again/);
    const incomplete = JSON.parse(golden);
    delete incomplete.portfolio.holdings;
    expect(() => parseSnapshot(JSON.stringify(incomplete))).toThrow(SnapshotError);
    expect(() => parseSnapshot(JSON.stringify(incomplete))).toThrow(/portfolio\.holdings/);
  });

  it('finds portfolios by name', () => {
    const snapshot = parseSnapshot(demo);
    const imaginary = snapshot.imaginary[0];
    expect(portfolioNamed(snapshot, '')).toBe(snapshot.portfolio);
    expect(portfolioNamed(snapshot, imaginary?.name ?? '')).toBe(imaginary);
    expect(portfolioNamed(snapshot, 'nope')).toBeUndefined();
  });
});
