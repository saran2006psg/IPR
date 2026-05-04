function decodeBasicHtmlEntities(text) {
  const named = {
    nbsp: ' ',
    amp: '&',
    lt: '<',
    gt: '>',
    quot: '"',
    apos: "'",
  };

  return text
    .replace(/&([a-z]+);/gi, (match, name) => named[name.toLowerCase()] ?? match)
    .replace(/&#(\d+);/g, (_, num) => String.fromCharCode(Number(num)))
    .replace(/&#x([0-9a-f]+);/gi, (_, hex) => String.fromCharCode(parseInt(hex, 16)));
}

export function cleanDisplayText(value) {
  if (value === null || value === undefined) {
    return '';
  }

  const original = String(value);
  let text = decodeBasicHtmlEntities(original);

  // Normalize common OCR and encoding artifacts.
  const replacements = [
    [/\u2018|\u2019/g, "'"],
    [/\u201c|\u201d/g, '"'],
    [/\u2013|\u2014/g, '-'],
    [/\u2026/g, '...'],
    [/\ufb00/g, 'ff'],
    [/\ufb01/g, 'fi'],
    [/\ufb02/g, 'fl'],
    [/\ufb03/g, 'ffi'],
    [/\ufb04/g, 'ffl'],
    [/\ufb05|\ufb06/g, 'st'],
    [/\u00a0/g, ' '],
    [/\u00ad/g, ''],
    [/\u2022|\u25cf|\u25aa|\u25e6/g, ' '],
    [/\u200e|\u200f/g, ''],
    [/â€™/g, "'"],
    [/â€œ|â€\u009d|â€\u009c|â€\x9d|â€\x9c/g, '"'],
    [/â€“|â€”/g, '-'],
    [/â€¦/g, '...'],
    [/â€¢/g, ' '],
    [/Â/g, ''],
    [/�/g, ''],
  ];

  for (const [pattern, replacement] of replacements) {
    text = text.replace(pattern, replacement);
  }

  // Drop invisible/control characters first.
  text = text
    .replace(/[\u200b-\u200d\ufeff]/g, '')
    .replace(/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/g, '')
    // Merge OCR line wraps/hyphenation artifacts.
    .replace(/([A-Za-z])\s*-\s+(?=[A-Za-z])/g, '$1')
    .replace(/\s*\n\s*/g, ' ');

  // Replace obviously noisy symbols with spaces while keeping legal text punctuation.
  text = text
    .replace(/[^A-Za-z0-9\s.,:;()'"/\-&%$]/g, ' ')
    .replace(/([.,:;()'"/\-&%$])\1{2,}/g, '$1')
    .replace(/\s+/g, ' ')
    .trim();

  // Token-level filtering to remove OCR gibberish chunks.
  const filteredTokens = text.split(' ').filter((token) => {
    if (!token) {
      return false;
    }

    if (token.length <= 2) {
      return /^[A-Za-z0-9]+$/.test(token);
    }

    const alnum = (token.match(/[A-Za-z0-9]/g) || []).length;
    const letters = (token.match(/[A-Za-z]/g) || []).length;
    const digits = (token.match(/[0-9]/g) || []).length;
    const punctuation = token.length - alnum;
    const hasSymbolNoise = /[~`!^*_+=|\\<>?{}\[\]]/.test(token);
    const repeatedCharNoise = /(.)\1{4,}/.test(token);
    const letterOnly = token.replace(/[^A-Za-z]/g, '');
    const hasNoVowelLongWord = letterOnly.length >= 10 && !/[aeiouyAEIOUY]/.test(letterOnly);

    if (hasSymbolNoise) {
      return false;
    }

    if (repeatedCharNoise) {
      return false;
    }

    if (alnum / token.length < 0.6) {
      return false;
    }

    if (letters === 0 && digits > 0) {
      return true;
    }

    if (letters > 0 && punctuation > 2 && letters < 4) {
      return false;
    }

    if (hasNoVowelLongWord) {
      return false;
    }

    return true;
  });

  text = filteredTokens.join(' ')
    .replace(/\s+([.,:;])/g, '$1')
    .replace(/\(\s+/g, '(')
    .replace(/\s+\)/g, ')')
    .replace(/\s+/g, ' ')
    .trim();

  // Avoid visually noisy punctuation runs from OCR errors.
  text = text.replace(/([!?.,])\1{2,}/g, '$1$1');

  // Safety fallback: avoid over-cleaning into empty/near-empty output.
  if (text.length < 8 && original.length > 20) {
    return original
      .replace(/[\u200b-\u200d\ufeff]/g, '')
      .replace(/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  return text;
}

export function cleanClauseDisplayText(value) {
  const original = value === null || value === undefined ? '' : String(value);
  if (!original) {
    return '';
  }

  let text = cleanDisplayText(original)
    // Keep clause numbering tidy, e.g., "1 . 2 ( a )" => "1.2(a)"
    .replace(/(\d)\s*\.\s*(\d)/g, '$1.$2')
    .replace(/\(\s*([A-Za-z0-9]+)\s*\)/g, '($1)')
    // Remove obvious OCR separators.
    .replace(/[|¦]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  // Drop suspicious one-character token runs often created by OCR segmentation.
  text = text
    .split(' ')
    .filter((token, idx, arr) => {
      if (token.length > 1) {
        return true;
      }

      const isAlphaNum = /^[A-Za-z0-9]$/.test(token);
      if (!isAlphaNum) {
        return false;
      }

      const prev = arr[idx - 1] || '';
      const next = arr[idx + 1] || '';
      const surroundedBySingles = prev.length === 1 && next.length === 1;
      return !surroundedBySingles;
    })
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim();

  // Safety fallback to avoid over-cleaning clauses.
  if (text.length < 20 && original.length > 40) {
    return cleanDisplayText(original);
  }

  return text;
}
