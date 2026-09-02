export type HighlightSegment = {
  text: string;
  match: boolean;
};

const EM_FRAGMENT = /<em>(.*?)<\/em>/gi;
const HTML_TAG = /<[^>]+>/g;

/** Parse Elasticsearch highlight fragments that wrap matches in <em> tags. */
export function parseEmHighlight(html: string): HighlightSegment[] {
  if (!html) {
    return [];
  }

  if (!/<em>/i.test(html)) {
    return [{ text: stripUnexpectedTags(html), match: false }];
  }

  const segments: HighlightSegment[] = [];
  let lastIndex = 0;
  EM_FRAGMENT.lastIndex = 0;

  for (const match of html.matchAll(EM_FRAGMENT)) {
    const index = match.index ?? 0;
    if (index > lastIndex) {
      const plain = stripUnexpectedTags(html.slice(lastIndex, index));
      if (plain) {
        segments.push({ text: plain, match: false });
      }
    }

    const highlighted = stripUnexpectedTags(match[1] ?? "");
    if (highlighted) {
      segments.push({ text: highlighted, match: true });
    }

    lastIndex = index + match[0].length;
  }

  if (lastIndex < html.length) {
    const plain = stripUnexpectedTags(html.slice(lastIndex));
    if (plain) {
      segments.push({ text: plain, match: false });
    }
  }

  return segments.length ? segments : [{ text: stripUnexpectedTags(html), match: false }];
}

export function truncateHighlightSegments(
  segments: HighlightSegment[],
  maxLength: number,
): HighlightSegment[] {
  if (maxLength <= 0 || segments.length === 0) {
    return [];
  }

  let remaining = maxLength;
  const result: HighlightSegment[] = [];

  for (const segment of segments) {
    if (remaining <= 0) {
      break;
    }

    if (segment.text.length <= remaining) {
      result.push(segment);
      remaining -= segment.text.length;
      continue;
    }

    const text = segment.text.slice(0, remaining).trimEnd();
    if (text) {
      result.push({ text, match: segment.match });
    }
    break;
  }

  return result;
}

function stripUnexpectedTags(text: string): string {
  return text.replace(HTML_TAG, "");
}
