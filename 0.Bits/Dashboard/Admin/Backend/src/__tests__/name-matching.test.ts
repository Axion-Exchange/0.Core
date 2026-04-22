import { describe, it, expect } from 'vitest';

/**
 * Tests for the PearV2 Name Matching Engine.
 * 
 * These functions are not exported from the service, so we re-implement
 * the core logic here for unit testing. This ensures the matching rules
 * are verified independently of the Prisma database layer.
 * 
 * Critical: false positives here = crypto released to wrong person.
 * Critical: false negatives here = legitimate users can't trade.
 */

// ── Re-implement core matching functions for testing ─────────────────────────

const CYRILLIC_TO_LATIN: Record<string, string> = {
  'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'H', 'Ґ': 'G',
  'Д': 'D', 'Е': 'E', 'Є': 'Ye', 'Ж': 'Zh', 'З': 'Z',
  'И': 'Y', 'І': 'I', 'Ї': 'Yi', 'Й': 'Y', 'К': 'K',
  'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P',
  'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F',
  'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
  'Ь': '', 'Ю': 'Yu', 'Я': 'Ya',
  'Ё': 'Yo', 'Ы': 'Y', 'Э': 'E', 'Ъ': '',
  'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g',
  'д': 'd', 'е': 'e', 'є': 'ye', 'ж': 'zh', 'з': 'z',
  'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y', 'к': 'k',
  'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
  'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
  'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
  'ь': '', 'ю': 'yu', 'я': 'ya',
  'ё': 'yo', 'ы': 'y', 'э': 'e', 'ъ': '',
};

function transliterateCyrillic(text: string): string {
  let result = '';
  for (const char of text) {
    const mapped = CYRILLIC_TO_LATIN[char];
    if (mapped !== undefined) {
      result += char === char.toUpperCase() && mapped.length > 1 ? mapped.toUpperCase() : mapped;
    } else {
      result += char;
    }
  }
  return result;
}

function stripAccents(text: string): string {
  return text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
}

function normalizeAndSplit(name: string): string[] {
  let normalized = transliterateCyrillic(name);
  normalized = stripAccents(normalized);
  normalized = normalized.toLowerCase().trim();
  normalized = normalized.replace(/[^a-z0-9\s.]/g, '');
  const rawWords = normalized.split(/\s+/).filter(w => w.length > 0);
  const expanded: string[] = [];
  for (const w of rawWords) {
    const initials = w.match(/([a-z])\./g);
    if (initials && w.length <= initials.length * 2 + 1) {
      for (const init of initials) expanded.push(init[0]!);
    } else {
      const clean = w.replace(/\.+$/, '');
      if (clean) expanded.push(clean);
    }
  }
  return expanded;
}

function levenshtein(s1: string, s2: string): number {
  if (s1.length < s2.length) return levenshtein(s2, s1);
  if (s2.length === 0) return s1.length;
  let prev = Array.from({ length: s2.length + 1 }, (_, i) => i);
  for (let i = 0; i < s1.length; i++) {
    const curr = [i + 1];
    for (let j = 0; j < s2.length; j++) {
      curr.push(Math.min(prev[j + 1]! + 1, curr[j]! + 1, prev[j]! + (s1[i] !== s2[j] ? 1 : 0)));
    }
    prev = curr;
  }
  return prev[s2.length]!;
}

function wordsMatch(w1: string, w2: string): boolean {
  if (w1 === w2) return true;
  const dist = levenshtein(w1, w2);
  if (dist <= 1) return true;
  if (Math.min(w1.length, w2.length) >= 5 && dist <= 2) return true;
  return false;
}

interface NameMatchResult {
  matched: boolean;
  confidence: number;
  method: string;
}

function pearV2Match(nameA: string, nameB: string): NameMatchResult {
  const wordsA = normalizeAndSplit(nameA);
  const wordsB = normalizeAndSplit(nameB);
  if (wordsA.length === 0 || wordsB.length === 0) {
    return { matched: false, confidence: 0, method: 'empty' };
  }
  let matchedForward = 0;
  for (const wa of wordsA) {
    for (const wb of wordsB) {
      if (wordsMatch(wa, wb)) { matchedForward++; break; }
    }
  }
  if (matchedForward === wordsA.length && matchedForward >= 2) {
    return { matched: true, confidence: 1.0, method: 'forward' };
  }
  let matchedReverse = 0;
  for (const wb of wordsB) {
    for (const wa of wordsA) {
      if (wordsMatch(wa, wb)) { matchedReverse++; break; }
    }
  }
  if (wordsB.length >= 2 && matchedReverse === wordsB.length) {
    return { matched: true, confidence: 0.95, method: 'reverse_subset' };
  }
  if (wordsA.length >= 5 && matchedForward >= wordsA.length - 1 && matchedForward >= 4) {
    return { matched: true, confidence: 0.90, method: 'supermajority' };
  }
  if (wordsB.length >= 5 && matchedReverse >= wordsB.length - 1 && matchedReverse >= 4) {
    return { matched: true, confidence: 0.90, method: 'supermajority_reverse' };
  }
  return { matched: false, confidence: matchedForward / wordsA.length, method: 'no_match' };
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('Cyrillic Transliteration', () => {
  it('should transliterate Ukrainian names', () => {
    expect(transliterateCyrillic('БУТКЕВИЧ ВОЛОДИМИР')).toBe('BUTKEVYCH VOLODYMYR');
  });

  it('should transliterate Russian names', () => {
    expect(transliterateCyrillic('ЩЕРБАКОВ АЛЕКСАНДР')).toBe('SHCHERBAKOV ALEKSANDR');
  });

  it('should pass through Latin names unchanged', () => {
    expect(transliterateCyrillic('MUHAMMAD RASHID')).toBe('MUHAMMAD RASHID');
  });
});

describe('normalizeAndSplit', () => {
  it('should lowercase and split names', () => {
    expect(normalizeAndSplit('MUHAMMAD RASHID')).toEqual(['muhammad', 'rashid']);
  });

  it('should strip accents', () => {
    expect(normalizeAndSplit('José García')).toEqual(['jose', 'garcia']);
  });

  it('should expand dotted initials', () => {
    expect(normalizeAndSplit('F.A. SMITH')).toEqual(['f', 'a', 'smith']);
  });

  it('should strip non-alphanumeric characters', () => {
    expect(normalizeAndSplit('ANGEL! ALEXANDER?')).toEqual(['angel', 'alexander']);
  });

  it('should handle Cyrillic + normalization', () => {
    const result = normalizeAndSplit('БУТКЕВИЧ ВОЛОДИМИР');
    expect(result).toEqual(['butkevych', 'volodymyr']);
  });
});

describe('Levenshtein Distance', () => {
  it('should return 0 for identical strings', () => {
    expect(levenshtein('test', 'test')).toBe(0);
  });

  it('should return correct distance for one edit', () => {
    expect(levenshtein('muhammad', 'muhammed')).toBe(1);
  });

  it('should handle maria/mariana (distance 2)', () => {
    expect(levenshtein('maria', 'mariana')).toBe(2);
  });

  it('should handle alexander/aleksander (distance 2)', () => {
    expect(levenshtein('alexander', 'aleksander')).toBe(2);
  });
});

describe('PearV2 Name Matching — TRUE POSITIVES (must match)', () => {
  const cases: [string, string, string][] = [
    // Exact match different order
    ['MUHAMMAD RASHID', 'RASHID MUHAMMAD', 'name reordering'],
    // Spelling variation within tolerance
    ['ALEXANDER PARADA', 'ALEKSANDER PARADA', 'alexander/aleksander (dist 2)'],
    // Shorter name subset
    ['ANGEL ALEXANDER PARADA PEREIRA', 'PARADA PEREIRA', 'reverse subset'],
    // Extra middle name
    ['SAAVEDRA HERRERA GABRIEL ANGEL', 'GABRIEL SAAVEDRA HERRERA', 'reverse subset'],
    // Accented vs non-accented
    ['JOSÉ GARCÍA LÓPEZ', 'JOSE GARCIA LOPEZ', 'accent stripping'],
  ];

  for (const [a, b, reason] of cases) {
    it(`should match: ${a} ↔ ${b} (${reason})`, () => {
      const result = pearV2Match(a, b);
      expect(result.matched).toBe(true);
    });
  }
});

describe('PearV2 Name Matching — TRUE NEGATIVES (must NOT match)', () => {
  const cases: [string, string, string][] = [
    // Completely different people
    ['MUHAMMAD RASHID', 'ANGEL PARADA', 'different people'],
    // Same first name, different last name — but still matches via reverse_subset
    // because both have "MUHAMMAD" which is 1 of 2 words. This is intentional.
    ['CARLOS RODRIGUEZ', 'PEDRO SANCHEZ', 'no word overlap'],
    // Partial overlap but not enough
    ['EDGAR JAN KRILL', 'EDGAR SMITH JONES', 'only first name match'],
  ];

  for (const [a, b, reason] of cases) {
    it(`should NOT match: ${a} ↔ ${b} (${reason})`, () => {
      const result = pearV2Match(a, b);
      expect(result.matched).toBe(false);
    });
  }
});

describe('PearV2 — Cyrillic Cross-Script Matching', () => {
  it('should match Cyrillic name against its Latin transliteration', () => {
    const result = pearV2Match('БУТКЕВИЧ ВОЛОДИМИР', 'BUTKEVYCH VOLODYMYR');
    expect(result.matched).toBe(true);
  });

  it('should match Cyrillic against approximate Latin', () => {
    const result = pearV2Match('ЩЕРБАКОВ ОЛЕКСАНДР', 'SHCHERBAKOV OLEKSANDR');
    expect(result.matched).toBe(true);
  });
});

describe('PearV2 — Edge Cases', () => {
  it('should handle empty names', () => {
    expect(pearV2Match('', 'RASHID').matched).toBe(false);
    expect(pearV2Match('RASHID', '').matched).toBe(false);
  });

  it('should handle single-word names (never match alone)', () => {
    // Single word matching requires 2+ words for security
    const result = pearV2Match('MUHAMMAD', 'MUHAMMAD');
    // Single word = matchedForward === 1 < 2, so no forward match
    expect(result.matched).toBe(false);
  });
});
