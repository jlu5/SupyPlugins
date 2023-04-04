#!/usr/bin/env python3
import argparse
import re
import sys

import mwparserfromhell

def fmt_node(w, summary=False):
    s = ''
    for node in w.nodes:
        if isinstance(node, mwparserfromhell.nodes.text.Text):
            text = str(node)
        elif isinstance(node, mwparserfromhell.nodes.tag.Tag):
            text = fmt_node(node.contents, summary=summary)
        elif isinstance(node, mwparserfromhell.nodes.wikilink.Wikilink):
            text = node.text or node.title
            if ':' in node.title:
                continue
        elif isinstance(node, mwparserfromhell.nodes.external_link.ExternalLink):
            text = node.title or node.url
        else:
            continue

        if s or text.strip():
            s += str(text)
        if summary:
            lines = s.lstrip().split('\n\n')
            if len(lines) > 1:
                s = lines[0]
                break
    return s.strip()

_RE_EMPTY_PARENTHESES = re.compile(r' ?\(\s+\)')
def _cleanup(text):
    """Attempt to clean up text a bit further."""
    text = re.sub(_RE_EMPTY_PARENTHESES, '', text)
    return text

def fmt(text, clean=True, **kwargs):
    w = mwparserfromhell.parse(text)
    output = fmt_node(w, **kwargs)
    if clean:
        output = _cleanup(output)
    return output

def main():
    parser = argparse.ArgumentParser(
        description="Generate plain text summaries from Wikitext input")
    parser.add_argument('--no-summary', '-ns', action='store_true',
        help='Return the whole page instead of just the first paragraph')
    args = parser.parse_args()

    result = fmt(sys.stdin.read(), summary=not args.no_summary)
    print(result)

if __name__ == '__main__':
    main()
