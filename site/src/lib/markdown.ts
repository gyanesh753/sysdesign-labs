// Markdown -> HTML for lectures, project briefs, notes and quiz text.
// renderLecture() additionally wraps every spoken sentence in <span class="s" data-s="N"> and returns the
// narration script, so the page, the browser voice and the generated audio all share one list of sentences.
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkDirective from 'remark-directive';
import remarkRehype from 'remark-rehype';
import rehypeSlug from 'rehype-slug';
import rehypeShiki from '@shikijs/rehype';
import rehypeStringify from 'rehype-stringify';
import { visit, SKIP } from 'unist-util-visit';

export type NarrationItem = { i: number; text: string; gap: number };
export type NarrationSection = { id: string; title: string; depth: number; items: NarrationItem[] };

// Seconds of silence after: a sentence, a paragraph or list item, a heading, a checkpoint question.
const GAP = { sentence: 0.28, block: 0.55, heading: 0.7, think: 1.8 };

// :::callout[Title]{type=warn}   :::checkpoint[Question]   :::spoken (heard, not shown)   :::silent (shown, not heard)
function directives() {
  return (tree: any) => {
    visit(tree, (node: any, index: number | undefined, parent: any) => {
      if (node.type === 'containerDirective') {
        const data = (node.data ??= {});
        const first = node.children[0];
        const label = first?.data?.directiveLabel ? first : null;
        if (node.name === 'checkpoint') {
          data.hName = 'details';
          data.hProperties = { className: ['checkpoint'] };
          if (label) label.data.hName = 'summary';
          else node.children.unshift({ type: 'paragraph', data: { hName: 'summary' }, children: [{ type: 'text', value: 'What would you answer?' }] });
        } else if (node.name === 'spoken') {
          data.hName = 'div';
          data.hProperties = { className: ['spoken-only'], hidden: true };
        } else if (node.name === 'silent') {
          data.hName = 'div';
          data.hProperties = { className: ['silent'] };
        } else {
          const kind = node.name === 'callout' ? (node.attributes?.type ?? 'note') : node.name;
          data.hName = 'aside';
          data.hProperties = { className: ['callout', `callout-${kind}`] };
          if (label) {
            label.data.hName = 'p';
            label.data.hProperties = { className: ['callout-title'] };
          }
        }
      } else if ((node.type === 'textDirective' || node.type === 'leafDirective') && parent && index !== undefined) {
        // Not a feature we use: put the literal text back so "1:many" or "a:b" survives.
        const prefix = node.type === 'textDirective' ? ':' : '::';
        const text = { type: 'text', value: prefix + node.name };
        const replacement = node.type === 'textDirective' ? [text, ...node.children] : [{ type: 'paragraph', children: [text, ...node.children] }];
        parent.children.splice(index, 1, ...replacement);
        return [SKIP, index];
      }
    });
  };
}

// ```mermaid fences become <pre class="mermaid"> for the client-side renderer.
function mermaidBlocks() {
  return (tree: any) => {
    visit(tree, 'element', (node: any) => {
      const code = node.tagName === 'pre' ? node.children?.[0] : null;
      if (code?.tagName === 'code' && code.properties?.className?.includes('language-mermaid')) {
        node.properties = { className: ['mermaid'] };
        node.children = [{ type: 'text', value: code.children.map((c: any) => c.value ?? '').join('') }];
      }
    });
  };
}

function wrapTables() {
  return (tree: any) => {
    visit(tree, 'element', (node: any, index: number | undefined, parent: any) => {
      if (node.tagName === 'table' && parent && index !== undefined) {
        parent.children[index] = { type: 'element', tagName: 'div', properties: { className: ['table-wrap'] }, children: [node] };
        return SKIP;
      }
    });
  };
}

const textOf = (node: any): string => (node.type === 'text' ? node.value : (node.children ?? []).map(textOf).join(''));
const BLOCK_TAGS = new Set(['p', 'ul', 'ol', 'pre', 'div', 'table', 'blockquote', 'details', 'aside', 'figure']);
const isBlock = (node: any) => node.type === 'element' && BLOCK_TAGS.has(node.tagName);
const SENTENCE_END = /(?<=[.?!]["')]?)\s+(?=["'(]?[A-Z0-9])/;

export function speakable(text: string, pronunciations: Record<string, string>): string {
  let t = text.replace(/\s+/g, ' ').trim();
  for (const [word, say] of Object.entries(pronunciations)) {
    t = t.replace(new RegExp(`(?<![\\w])${word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\w])`, 'g'), say);
  }
  return t;
}

// Wrap sentences and collect the narration script into file.data.narration.
function narrate() {
  return (tree: any, file: any) => {
    const pron: Record<string, string> = file.data.pronunciations ?? {};
    const sections: NarrationSection[] = [];
    let current: NarrationSection = { id: 'intro', title: 'Introduction', depth: 2, items: [] };
    let n = 0;

    const span = (children: any[], prefix = '', gap = GAP.sentence) => {
      const visible = textOf({ children }).replace(/\s+/g, ' ').trim();
      if (!visible) return null;
      const text = speakable(prefix + visible, pron);
      const properties: Record<string, unknown> = { className: ['s'], dataS: n };
      if (text !== visible) properties.dataSay = text;
      current.items.push({ i: n++, text, gap });
      return { type: 'element', tagName: 'span', properties, children };
    };
    const endBlock = (gap = GAP.block) => {
      const last = current.items.at(-1);
      if (last) last.gap = Math.max(last.gap, gap);
    };
    const sentences = (el: any, prefix = '') => {
      const groups: any[][] = [[]];
      for (const child of el.children) {
        if (child.type !== 'text') groups.at(-1)!.push(child);
        else
          child.value.split(SENTENCE_END).forEach((part: string, k: number) => {
            if (k > 0) groups.push([]);
            if (part) groups.at(-1)!.push({ type: 'text', value: part });
          });
      }
      const out: any[] = [];
      groups.forEach((group, k) => {
        if (k > 0) out.push({ type: 'text', value: ' ' });
        const s = span(group, k === 0 ? prefix : '');
        if (s) out.push(s);
        else out.push(...group);
      });
      el.children = out;
    };

    const walk = (node: any) => {
      if (node.type !== 'element') return;
      const tag: string = node.tagName;
      const cls: string[] = node.properties?.className ?? [];
      if (tag === 'pre' || tag === 'table' || cls.includes('silent')) return;
      if (tag === 'h2' || tag === 'h3') {
        if (current.items.length) sections.push(current);
        current = { id: String(node.properties?.id ?? `section-${sections.length + 1}`), title: textOf(node).trim(), depth: Number(tag[1]), items: [] };
        const s = span(node.children, '', GAP.heading);
        if (s) node.children = [s];
        return;
      }
      if (/^h[4-6]$/.test(tag)) {
        const s = span(node.children, '', GAP.heading);
        if (s) node.children = [s];
        return;
      }
      if (tag === 'p' || (tag === 'li' && !node.children.some(isBlock))) {
        sentences(node);
        endBlock();
        return;
      }
      if (tag === 'summary') {
        sentences(node, 'Check yourself. ');
        endBlock(GAP.think);
        return;
      }
      if (tag === 'li') {
        // Text mixed with nested blocks: each run of inline content is one spoken item.
        const out: any[] = [];
        let run: any[] = [];
        const flush = () => {
          if (!run.length) return;
          const s = span(run);
          if (s) out.push(s);
          else out.push(...run);
          endBlock();
          run = [];
        };
        for (const child of node.children) {
          if (isBlock(child)) {
            flush();
            walk(child);
            out.push(child);
          } else run.push(child);
        }
        flush();
        node.children = out;
        return;
      }
      for (const child of node.children) walk(child);
    };

    for (const child of tree.children) walk(child);
    if (current.items.length) sections.push(current);
    file.data.narration = sections;
  };
}

const processors = new Map<string, any>();

function processor(idPrefix: string, withNarration: boolean) {
  const key = `${idPrefix}|${withNarration}`;
  let p = processors.get(key);
  if (!p) {
    p = unified().use(remarkParse).use(remarkGfm).use(remarkDirective).use(directives).use(remarkRehype).use(rehypeSlug, { prefix: idPrefix }).use(mermaidBlocks).use(wrapTables);
    if (withNarration) p = p.use(narrate);
    p = p.use(rehypeShiki, { themes: { light: 'github-light', dark: 'github-dark' }, defaultLanguage: 'text', fallbackLanguage: 'text' }).use(rehypeStringify);
    processors.set(key, p);
  }
  return p;
}

export async function renderMarkdown(markdown: string, idPrefix = ''): Promise<string> {
  return String(await processor(idPrefix, false).process(markdown));
}

export async function renderLecture(markdown: string, pronunciations: Record<string, string> = {}): Promise<{ html: string; sections: NarrationSection[] }> {
  const file = await processor('', true).process({ value: markdown, data: { pronunciations } });
  return { html: String(file), sections: file.data.narration as NarrationSection[] };
}

/** For one-line text such as a quiz option: drop the wrapping <p>. */
export async function renderInline(markdown: string): Promise<string> {
  const html = (await renderMarkdown(markdown, 'q-')).trim();
  const m = /^<p>([\s\S]*)<\/p>$/.exec(html);
  return m && !m[1].includes('<p>') ? m[1] : html;
}
