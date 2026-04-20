import { createLogger } from '../../lib/logger.js';

const log = createLogger('name-matcher');

export interface MatchResult {
  matched: boolean;
  confidence: number;
  method: string;
  binanceName: string;
  paymentName: string;
  details: string;
}

/**
 * NameMatcherService
 * Matches Binance P2P buyer names against fiat EUR payment sender names.
 * Uses hardcoded Levenshtein fuzzy matching ONLY. 
 * Replaces PearV2 Python's `name_matcher.py` explicitly avoiding AI hallucination models.
 */
export class NameMatcherService {

  public match(binanceName: string, paymentName: string): MatchResult {
    const bWords = this.normalizeAndSplit(binanceName);
    const pWords = this.normalizeAndSplit(paymentName);

    if (bWords.length === 0 || pWords.length === 0) {
      return {
        matched: false,
        confidence: 0.0,
        method: 'hardcoded',
        binanceName,
        paymentName,
        details: 'Empty name(s)',
      };
    }

    let matchedWords = 0;
    const unmatched: string[] = [];

    // Forward check: Do all Binance terms exist in the Payment name?
    for (const bWord of bWords) {
      let found = false;
      for (const pWord of pWords) {
        if (this.wordsMatch(bWord, pWord)) {
          found = true;
          break;
        }
      }
      if (found) {
        matchedWords++;
      } else {
        unmatched.push(bWord);
      }
    }

    if (matchedWords === bWords.length) {
      return {
        matched: true,
        confidence: 1.0,
        method: 'hardcoded',
        binanceName,
        paymentName,
        details: `All ${matchedWords} words matched`,
      };
    }

    // Reverse check: shortened Bank names. Do all Payment words exist securely in Binance name?
    let matchedPaymentWords = 0;
    for (const pWord of pWords) {
      let found = false;
      for (const bWord of bWords) {
        if (this.wordsMatch(bWord, pWord)) {
          found = true;
          break;
        }
      }
      if (found) matchedPaymentWords++;
    }

    if (pWords.length >= 2 && matchedPaymentWords === pWords.length) {
      return {
        matched: true,
        confidence: 0.95,
        method: 'hardcoded_reverse',
        binanceName,
        paymentName,
        details: `All ${pWords.length} payment words found safely inside Binance name footprint`,
      };
    }

    // Threshold Fallback Check (>= 75% overlap on shorthand)
    const thresholdResult = this.thresholdMatch(bWords, pWords, binanceName, paymentName);
    if (thresholdResult.matched) {
      return thresholdResult;
    }

    const confidence = matchedWords / bWords.length;
    return {
      matched: false,
      confidence,
      method: 'hardcoded',
      binanceName,
      paymentName,
      details: `Missing words: ${unmatched.join(', ')} (Threshold fallback failed)`,
    };
  }

  private normalizeAndSplit(name: string): string[] {
    return name
      .toLowerCase()
      .trim()
      .split(/\s+/)
      .filter((w) => w.length > 0);
  }

  private wordsMatch(word1: string, word2: string): boolean {
    if (word1 === word2) return true;
    
    // Check spelling limit
    const dist = this.levenshteinDistance(word1, word2);
    if (dist <= 1) return true;

    // Abbreviations check: if one word is just initial
    if (word1.length === 1 && word2.length > 1 && word1[0] === word2[0]) return true;
    if (word2.length === 1 && word1.length > 1 && word2[0] === word1[0]) return true;

    return false;
  }

  private levenshteinDistance(s1: string, s2: string): number {
    if (s1.length < s2.length) return this.levenshteinDistance(s2, s1);
    if (s2.length === 0) return s1.length;

    let previousRow = Array.from({ length: s2.length + 1 }, (_, i) => i);
    
    for (let i = 0; i < s1.length; i++) {
        const c1 = s1[i] as string;
        const currentRow: number[] = [i + 1];
        for (let j = 0; j < s2.length; j++) {
            const c2 = s2[j] as string;
            const insertions = previousRow[j + 1]! + 1;
            const deletions = currentRow[j]! + 1;
            const substitutions = previousRow[j]! + (c1 !== c2 ? 1 : 0);
            currentRow.push(Math.min(insertions, deletions, substitutions));
        }
        previousRow = currentRow;
    }
    return previousRow[previousRow.length - 1]!;
  }

  private thresholdMatch(
    bWords: string[], 
    pWords: string[], 
    binanceName: string, 
    paymentName: string
  ): MatchResult {
    const shorter = Math.min(bWords.length, pWords.length);
    if (shorter < 2) {
      return {
        matched: false,
        confidence: 0.0,
        method: 'threshold_match',
        binanceName,
        paymentName,
        details: 'Names too short for secure threshold subset match',
      };
    }

    const shorterList = bWords.length <= pWords.length ? bWords : pWords;
    const longerList = pWords.length >= bWords.length ? pWords : bWords;
    
    let matchedWords = 0;
    const usedIndices = new Set<number>();

    for (const sWord of shorterList) {
      for (let i = 0; i < longerList.length; i++) {
        if (!usedIndices.has(i) && this.wordsMatch(sWord, longerList[i]!)) {
          matchedWords++;
          usedIndices.add(i);
          break;
        }
      }
    }

    const ratio = matchedWords / shorter;

    if (matchedWords >= 2 && ratio >= 0.75) {
      return {
        matched: true,
        confidence: parseFloat(ratio.toFixed(2)),
        method: 'threshold_match',
        binanceName,
        paymentName,
        details: `Threshold match: ${matchedWords}/${shorter} words matched (${(ratio * 100).toFixed(0)}%)`
      };
    }

    return {
      matched: false,
      confidence: parseFloat(ratio.toFixed(2)),
      method: 'threshold_match',
      binanceName,
      paymentName,
      details: `Threshold match failed: ${matchedWords}/${shorter} words matched (${(ratio * 100).toFixed(0)}%)`
    };
  }
}

export const nameMatcherService = new NameMatcherService();
