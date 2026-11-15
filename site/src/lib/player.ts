// Lecture player. Two engines behind one bar: generated audio files (with exact sentence timings)
// and the browser's own voice as a fallback when a chapter has no up-to-date audio.
import { getChapter, updateChapter } from './progress.ts';

type Section = { id: string; title: string; first: number; count: number; file?: string; duration?: number; starts?: number[] };
export type Playlist = { mode: 'files' | 'speech'; base: string; total: number; minutes: number; sections: Section[] };

const RATE_KEY = 'sysdesign-labs-rate';
const fmt = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

export function initPlayer(opts: { chapterId: string; chapterTitle: string; article: HTMLElement; bar: HTMLElement; playlist: Playlist; onFinished: () => void }) {
  const { chapterId, article, bar, playlist } = opts;
  const $ = <T extends HTMLElement>(sel: string) => bar.querySelector<T>(sel)!;
  const spans = new Map<number, HTMLElement>();
  for (const el of article.querySelectorAll<HTMLElement>('[data-s]')) spans.set(Number(el.dataset.s), el);
  const total = playlist.total;
  const sectionOf = (i: number) => playlist.sections.findLast((s) => s.first <= i) ?? playlist.sections[0];
  const offsets: number[] = [];
  let sum = 0;
  for (const s of playlist.sections) {
    offsets.push(sum);
    sum += s.duration ?? 0;
  }

  let i = Math.min(getChapter(chapterId).listenAt ?? 0, total - 1);
  let playing = false;
  let lastUserScroll = 0;
  let useFiles = playlist.mode === 'files';
  let rate = 1;
  try {
    rate = Number(localStorage.getItem(RATE_KEY)) || 1;
  } catch {}
  const rateSelect = $<HTMLSelectElement>('[data-rate]');
  rateSelect.value = String(rate);
  if (!rateSelect.value) rateSelect.value = '1';

  /* ----- painting ----- */
  let shown: HTMLElement | null = null;
  function paint(follow = false) {
    shown?.classList.remove('speaking', 'speaking-block');
    shown = null;
    const el = spans.get(i);
    if (el && playing) {
      const hiddenHost = el.closest<HTMLElement>('.spoken-only');
      const target = hiddenHost ? (hiddenHost.previousElementSibling as HTMLElement | null) : el;
      el.closest('details')?.setAttribute('open', '');
      if (target) {
        target.classList.add(hiddenHost ? 'speaking-block' : 'speaking');
        shown = target;
        if (follow && Date.now() - lastUserScroll > 4000) {
          const r = target.getBoundingClientRect();
          if (r.top < innerHeight * 0.15 || r.bottom > innerHeight * 0.7) target.scrollIntoView({ block: 'center', behavior: 'smooth' });
        }
      }
    }
    const sec = sectionOf(i);
    $('[data-sec]').textContent = sec.title;
    $('[data-play] path').setAttribute('d', playing ? 'M3 2h4v12H3zM9 2h4v12H9z' : 'M3 1.5v13l11-6.5z');
    $('[data-play]').setAttribute('aria-label', playing ? 'Pause' : 'Play');
    document.dispatchEvent(new CustomEvent('player:section', { detail: sec.id }));
    paintTime();
  }
  function paintTime() {
    if (useFiles) {
      const k = playlist.sections.indexOf(sectionOf(i));
      const within = audio.src && currentSection === playlist.sections[k] ? audio.currentTime : (playlist.sections[k].starts?.[i - playlist.sections[k].first] ?? 0);
      const t = offsets[k] + within;
      $('[data-count]').textContent = `${fmt(t)} / ${fmt(sum)}`;
      $<HTMLElement>('[data-track]').style.width = `${(100 * t) / sum}%`;
    } else {
      $('[data-count]').textContent = `${i + 1} / ${total}`;
      $<HTMLElement>('[data-track]').style.width = `${(100 * i) / total}%`;
    }
  }
  function setIndex(n: number, follow: boolean) {
    if (n === i && shown) return;
    i = n;
    updateChapter(chapterId, (c) => (c.listenAt = i));
    paint(follow);
  }
  function finished() {
    playing = false;
    i = 0;
    updateChapter(chapterId, (c) => (c.listenAt = 0));
    paint();
    opts.onFinished();
  }

  /* ----- engine: audio files ----- */
  const audio = new Audio();
  audio.preload = 'auto';
  let currentSection: Section | null = null;
  let raf = 0;
  function tick() {
    if (!playing || !useFiles || !currentSection) return;
    if (audio.readyState < 1 || audio.seeking) {
      raf = requestAnimationFrame(tick);
      return;
    }
    const starts = currentSection.starts!;
    const t = audio.currentTime + 0.03;
    let k = 0;
    while (k + 1 < starts.length && starts[k + 1] <= t) k++;
    setIndex(currentSection.first + k, true);
    paintTime();
    raf = requestAnimationFrame(tick);
  }
  let fileReq = 0;
  function playFile(from: number) {
    const sec = sectionOf(from);
    const at = sec.starts![from - sec.first] ?? 0;
    const req = ++fileReq;
    // Only the most recent request may start playback: fast skipping queues several of these.
    const start = () => {
      if (req !== fileReq || !playing) return;
      audio.currentTime = at;
      audio.playbackRate = rate;
      audio.play().then(() => {
        if (req !== fileReq) return;
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(tick);
      }).catch((err: DOMException) => {
        // AbortError just means a newer play/pause replaced this one; it is not a failure.
        if (err.name === 'AbortError' || req !== fileReq) return;
        if (err.name === 'NotAllowedError') return pause();
        fallBackToSpeech();
      });
    };
    if (currentSection !== sec) {
      currentSection = sec;
      audio.src = playlist.base + sec.file;
      audio.load();
    }
    if (audio.readyState >= 1) start();
    else audio.addEventListener('loadedmetadata', start, { once: true });
  }
  audio.addEventListener('ended', () => {
    if (!playing || !currentSection) return;
    const next = playlist.sections[playlist.sections.indexOf(currentSection) + 1];
    if (!next) return finished();
    setIndex(next.first, true);
    playFile(next.first);
  });
  audio.addEventListener('error', () => {
    if (playing && useFiles) fallBackToSpeech();
  });
  function fallBackToSpeech() {
    useFiles = false;
    $('[data-note]').textContent = 'audio file unavailable, using the browser voice';
    if (playing) speak();
  }

  /* ----- engine: browser voice ----- */
  let token = 0;
  let silent = !('speechSynthesis' in window);
  function speak() {
    if (!playing) return;
    if (i >= total) return finished();
    paint(true);
    const mine = ++token;
    const el = spans.get(i);
    const text = el?.dataset.say ?? el?.textContent ?? '';
    const advance = () => {
      if (mine !== token || !playing) return;
      if (i + 1 >= total) return finished();
      setIndex(i + 1, true);
      speak();
    };
    const timer = () => setTimeout(advance, (text.length * 58) / rate);
    if (silent) return void timer();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = rate;
    let started = false;
    u.onstart = () => (started = true);
    u.onend = advance;
    u.onerror = () => {
      if (mine === token && !started) {
        silent = true;
        $('[data-note]').textContent = 'no voice in this browser, showing the highlight only';
        timer();
      }
    };
    speechSynthesis.speak(u);
  }

  /* ----- controls ----- */
  function stopSound() {
    token++;
    fileReq++;
    cancelAnimationFrame(raf);
    audio.pause();
    if ('speechSynthesis' in window) speechSynthesis.cancel();
  }
  function pause() {
    if (!playing) return;
    playing = false;
    stopSound();
    paint();
  }
  function play(from = i) {
    stopSound();
    i = Math.max(0, Math.min(total - 1, from));
    playing = true;
    bar.hidden = false;
    article.classList.add('listening');
    paint(true);
    if (useFiles) playFile(i);
    else speak();
    if ('mediaSession' in navigator) {
      navigator.mediaSession.metadata = new MediaMetadata({ title: opts.chapterTitle, artist: 'Sysdesign Labs' });
      navigator.mediaSession.setActionHandler('play', () => play());
      navigator.mediaSession.setActionHandler('pause', pause);
      navigator.mediaSession.setActionHandler('previoustrack', () => jump(-1));
      navigator.mediaSession.setActionHandler('nexttrack', () => jump(1));
    }
  }
  function jump(delta: number) {
    const n = Math.max(0, Math.min(total - 1, i + delta));
    if (playing) play(n);
    else {
      i = n;
      updateChapter(chapterId, (c) => (c.listenAt = i));
      paint();
    }
  }
  function close() {
    pause();
    bar.hidden = true;
    article.classList.remove('listening');
  }

  $('[data-play]').addEventListener('click', () => (playing ? pause() : play()));
  $('[data-prev]').addEventListener('click', () => jump(-1));
  $('[data-next]').addEventListener('click', () => jump(1));
  $('[data-close]').addEventListener('click', () => {
    close();
    document.dispatchEvent(new CustomEvent('progresschange'));
  });
  rateSelect.addEventListener('change', () => {
    rate = Number(rateSelect.value);
    try {
      localStorage.setItem(RATE_KEY, String(rate));
    } catch {}
    audio.playbackRate = rate;
    if (playing && !useFiles) play(i);
  });
  article.addEventListener('click', (e) => {
    if (bar.hidden) return;
    const target = e.target as HTMLElement;
    if (target.closest('a, button, summary')) return;
    const s = target.closest<HTMLElement>('[data-s]');
    if (s) play(Number(s.dataset.s));
  });
  for (const type of ['wheel', 'touchmove', 'keydown'] as const) addEventListener(type, () => (lastUserScroll = Date.now()), { passive: true });
  addEventListener('pagehide', stopSound);

  return { play, pause, close, isPlaying: () => playing, position: () => i, isActive: () => !bar.hidden };
}
