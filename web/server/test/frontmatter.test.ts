import { describe, expect, it } from 'vitest';
import { parseFrontmatter } from '../src/lib/frontmatter';

describe('parseFrontmatter', () => {
  it('parses a standard --- fenced YAML block', () => {
    const raw = '---\nname: foo\ndomain: docs\ntags: [a, b]\n---\n# Title\n\nbody text\n';
    const { data, body } = parseFrontmatter(raw);
    expect(data).toEqual({ name: 'foo', domain: 'docs', tags: ['a', 'b'] });
    expect(body).toBe('# Title\n\nbody text\n');
  });

  it('returns empty data when there is no frontmatter', () => {
    const raw = '# Just a heading\n\nno frontmatter here';
    const { data, body } = parseFrontmatter(raw);
    expect(data).toEqual({});
    expect(body).toBe(raw);
  });

  it('tolerates malformed YAML without throwing (data = {})', () => {
    const raw = '---\nname: foo\n  bad: : indent\n:::garbage\n---\nbody';
    const { data, body } = parseFrontmatter(raw);
    expect(data).toEqual({});
    expect(body).toBe('body');
  });

  it('preserves the raw input verbatim', () => {
    const raw = '---\nname: x\n---\nhello';
    expect(parseFrontmatter(raw).raw).toBe(raw);
  });

  it('treats a non-object YAML scalar frontmatter as empty data', () => {
    const raw = '---\njust a string\n---\nbody';
    expect(parseFrontmatter(raw).data).toEqual({});
  });
});
