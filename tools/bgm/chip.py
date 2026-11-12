"""EvoTail BGM 칩튠 합성기 (numpy). 곡 = 코드 진행 + 손으로 쓴 멜로디 + 자동 베이스·아르페지오·드럼.
렌더 결과는 끊김 없이 반복되는 루프(.ogg)."""
import math, re, subprocess
import numpy as np

SR = 44100
NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
QUAL = {'': (0, 4, 7), 'm': (0, 3, 7), '7': (0, 4, 7, 10), 'maj7': (0, 4, 7, 11), 'm7': (0, 3, 7, 10),
        'sus4': (0, 5, 7), 'sus2': (0, 2, 7), 'dim': (0, 3, 6), 'aug': (0, 4, 8), 'add9': (0, 4, 7, 14), '6': (0, 4, 7, 9)}


def midi(name):
    m = re.fullmatch(r'([A-G])([#b]?)(-?\d)', name)
    n = NOTE[m.group(1)] + {'#': 1, 'b': -1, '': 0}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + n


def hz(m): return 440.0 * 2 ** ((m - 69) / 12)


def chord(sym):
    """'Am7' → (근음 pitch class, [음정])"""
    m = re.fullmatch(r'([A-G][#b]?)(.*?)(?:/([A-G][#b]?))?', sym)
    root = NOTE[m.group(1)[0]] + {'#': 1, 'b': -1}.get(m.group(1)[1:], 0)
    bass = None
    if m.group(3): bass = NOTE[m.group(3)[0]] + {'#': 1, 'b': -1}.get(m.group(3)[1:], 0)
    return root % 12, QUAL[m.group(2)], (bass if bass is not None else root) % 12


def parse_line(text):
    """'C5:.5 E5:1 r:1 [C5 E5]:2' → [(시작 박, 길이 박, [midi])]"""
    out, t = [], 0.0
    for tok in text.split():
        if tok.startswith('|'): continue
        name, dur = tok.rsplit(':', 1); d = float(dur)
        if name != 'r':
            names = name.strip('[]').split('+')
            out.append((t, d, [midi(n) for n in names]))
        t += d
    return out, t


# ---------- 파형 ----------
def osc(kind, f, n, duty=.5, phase0=0.0, vib=0.0, vib_rate=5.5, vib_delay=.15):
    t = np.arange(n) / SR
    fm = f * (1 + vib * np.sin(2 * np.pi * vib_rate * t) * np.clip((t - vib_delay) / .2, 0, 1)) if vib else np.full(n, f)
    ph = (phase0 + np.cumsum(fm) / SR) % 1.0
    if kind == 'pulse': return np.where(ph < duty, 1.0, -1.0)
    if kind == 'tri': return 4 * np.abs(ph - .5) - 1
    if kind == 'saw': return 2 * ph - 1
    if kind == 'sine': return np.sin(2 * np.pi * ph)
    raise ValueError(kind)


def env(n, a=.005, d=.08, s=.6, r=.06, hold=None):
    """hold = 소리가 눌려 있는 샘플 수 (그 뒤 release)"""
    hold = n if hold is None else hold
    e = np.empty(n)
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    i = np.arange(n)
    e[:] = s
    if A: e[:min(A, n)] = np.linspace(0, 1, min(A, n), endpoint=False)
    if D:
        seg = slice(A, min(A + D, n))
        e[seg] = 1 - (1 - s) * (np.arange(seg.stop - seg.start) / D)
    rel = i >= hold
    if rel.any():
        lvl = e[min(hold, n - 1) - 1] if hold > 0 else 0
        e[rel] = lvl * np.clip(1 - (i[rel] - hold) / max(R, 1), 0, 1)
    return e


def noise(n, rng, tone=False):
    if tone:   # 짧은 주기 노이즈 (금속성)
        base = rng.uniform(-1, 1, 93); return np.tile(base, n // 93 + 1)[:n]
    return rng.uniform(-1, 1, n)


def lowpass(x, cutoff):
    a = math.exp(-2 * math.pi * cutoff / SR)
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x)


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


# ---------- 렌더 ----------
class Song:
    def __init__(self, name, bpm, bars, beats=4, swing=0.0):
        self.name, self.bpm, self.bars, self.beats, self.swing = name, bpm, bars, beats, swing
        self.spb = 60.0 / bpm
        self.length = bars * beats
        self.N = int(round(self.length * self.spb * SR))
        self.tail = int(2.0 * SR)
        self.L = np.zeros(self.N + self.tail); self.R = np.zeros(self.N + self.tail)
        self.rng = np.random.default_rng(3)

    def smp(self, beat):
        b = beat
        if self.swing and (beat * 2) % 2 == 1:       # 8분 뒷박 스윙
            b = beat + self.swing * .5
        return int(round(b * self.spb * SR))

    def add(self, sig, start, pan=0.0, gain=1.0):
        s = self.smp(start) if isinstance(start, float) or isinstance(start, int) else start
        e = s + len(sig)
        if e > len(self.L): sig = sig[:len(self.L) - s]; e = len(self.L)
        self.L[s:e] += sig * gain * (1 - max(0, pan)); self.R[s:e] += sig * gain * (1 + min(0, pan))

    def note(self, start, dur, m, kind='pulse', duty=.5, gain=.2, pan=0.0, a=.005, d=.08, s=.6, r=.08, vib=0.0,
             legato=.92, octave=0, detune=0.0, slide_from=None):
        hold = int(dur * self.spb * SR * legato)
        n = hold + int(r * SR) + 10
        f = hz(m + 12 * octave)
        w = osc(kind, f, n, duty, vib=vib)
        if detune: w = .6 * w + .4 * osc(kind, f * (1 + detune), n, duty, vib=vib)
        self.add(w * env(n, a, d, s, r, hold), start, pan, gain)

    # --- 악기 묶음 ---
    def melody(self, text, start=0.0, **kw):
        notes, length = parse_line(text)
        for t, d, ms in notes:
            for m in ms: self.note(start + t, d, m, **kw)
        return length

    def chords(self, prog, fn, start=0.0, bar_beats=None):
        bb = bar_beats or self.beats
        for i, sym in enumerate(prog):
            for part in [sym] if ' ' not in sym else [sym]:
                pass
            # 한 마디에 코드 두 개: "C G"
            syms = sym.split()
            per = bb / len(syms)
            for j, sy in enumerate(syms):
                fn(start + i * bb + j * per, per, chord(sy))

    def drum(self, kind, start, gain=.3, pan=0.0):
        rng = self.rng
        if kind == 'k':      # 킥: 떨어지는 사인
            n = int(.16 * SR); t = np.arange(n) / SR
            f = 120 * np.exp(-t * 28) + 42
            w = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18)
        elif kind == 's':    # 스네어: 노이즈 + 톤
            n = int(.14 * SR); t = np.arange(n) / SR
            w = (.7 * highpass(noise(n, rng), 1200) + .3 * np.sin(2 * np.pi * 190 * t)) * np.exp(-t * 26)
        elif kind == 'h':    # 닫힌 하이햇
            n = int(.04 * SR); t = np.arange(n) / SR
            w = highpass(noise(n, rng), 6000) * np.exp(-t * 90) * .7
        elif kind == 'o':    # 열린 하이햇
            n = int(.18 * SR); t = np.arange(n) / SR
            w = highpass(noise(n, rng), 5000) * np.exp(-t * 18) * .5
        elif kind == 'c':    # 크래시
            n = int(.9 * SR); t = np.arange(n) / SR
            w = highpass(noise(n, rng), 3000) * np.exp(-t * 4) * .45
        elif kind == 't':    # 탐 (낮은 톤)
            n = int(.18 * SR); t = np.arange(n) / SR
            f = 160 * np.exp(-t * 6) + 70
            w = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
        elif kind == 'b':    # 쉐이커/브러시
            n = int(.05 * SR); t = np.arange(n) / SR
            w = highpass(noise(n, rng), 4000) * np.sin(np.pi * np.clip(t / .05, 0, 1)) * .5
        else: return
        self.add(w, start, pan, gain)

    def drums(self, pattern, bars=None, start=0.0, step=.25, gains=None, every=None):
        """pattern: 마디 하나 16칸 문자열들 dict {'k': 'x...x...', ...} 또는 여러 줄 문자열 'k:x...|s:....' """
        gains = gains or {'k': .55, 's': .32, 'h': .12, 'o': .12, 'c': .25, 't': .35, 'b': .14}
        bars = bars or self.bars
        for b in range(bars):
            if every and not every(b): continue
            for kind, row in pattern.items():
                for i, ch in enumerate(row):
                    if ch in 'xX':
                        self.drum(kind, start + b * self.beats + i * step, gains[kind] * (1.25 if ch == 'X' else 1))

    def finish(self, out, echo=(.32, .22), lp=9000, master=.9, loop=True, rms=.15):
        L, R = self.L.copy(), self.R.copy()
        if loop:   # 끝의 꼬리를 앞쪽에 겹쳐 끊김 없는 루프
            L[:self.tail] += L[self.N:]; R[:self.tail] += R[self.N:]
            L, R = L[:self.N], R[:self.N]
        else:      # 짧은 효과음악: 소리 끝난 뒤 빈 부분은 자르고 끝을 부드럽게
            amp = np.maximum(np.abs(L), np.abs(R)); idx = np.nonzero(amp > 1e-3 * amp.max())[0]
            end = min(len(L), idx[-1] + int(.4 * SR)); L, R = L[:end], R[:end]
            fade = np.linspace(1, 0, int(.3 * SR)); L[-len(fade):] *= fade; R[-len(fade):] *= fade
        if echo:   # 간단한 핑퐁 에코 (루프 안에서 순환)
            dly, fb = int(echo[0] * self.spb * SR), echo[1]
            l2, r2 = L.copy(), R.copy()
            for k in range(1, 4):
                g = fb ** k
                (l2 if k % 2 else r2)[:] += np.roll(R if k % 2 else L, dly * k) * g if loop else np.concatenate([np.zeros(dly * k), (R if k % 2 else L)[:-dly * k]]) * g
            L, R = l2, r2
        L, R = lowpass(L, lp), lowpass(R, lp)
        L, R = highpass(L, 30), highpass(R, 30)
        peak = max(np.abs(L).max(), np.abs(R).max(), 1e-6)
        cur = math.sqrt(float((L ** 2 + R ** 2).mean() / 2)) or 1e-6
        g = min(master / peak, rms / cur)          # 곡마다 비슷한 크기 (봉우리는 master 넘지 않게)
        L, R = L * g, R * g
        data = (np.stack([L, R], 1) * 32767).astype('<i2')
        wav = out.rsplit('.', 1)[0] + '.wav'
        import wave
        with wave.open(wav, 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-c:a', 'libvorbis', '-q:a', '5', out], check=True)
        mp3 = out.rsplit('.', 1)[0] + '.mp3'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-c:a', 'libmp3lame', '-q:a', '3', mp3], check=True)
        return len(L) / SR


# ---------- 자동 반주 ----------
def bass_fn(song, style='rootfifth', octave=2, kind='tri', gain=.34, duty=.5):
    def f(start, length, ch):
        root, iv, bass = ch
        rm = 12 * (octave + 1) + bass
        fifth = 12 * (octave + 1) + (root + 7) % 12
        if fifth < rm: fifth += 12
        if style == 'rootfifth':
            pat = [(0, rm), (1, fifth), (2, rm), (3, fifth)]
        elif style == 'bounce':
            pat = [(0, rm), (.5, rm + 12), (1, rm), (1.5, rm + 12), (2, rm), (2.5, rm + 12), (3, rm), (3.5, rm + 12)]
        elif style == 'whole':
            pat = [(0, rm)]
        elif style == 'half':
            pat = [(0, rm), (2, fifth)]
        elif style == 'drive':
            pat = [(i * .5, rm) for i in range(8)]
        elif style == 'waltz':
            pat = [(0, rm)]
        elif style == 'walk':
            third = 12 * (octave + 1) + (root + iv[1]) % 12
            if third < rm: third += 12
            pat = [(0, rm), (1, third), (2, fifth), (3, third)]
        else: raise ValueError(style)
        step = {'bounce': .5, 'drive': .5, 'whole': length, 'half': 2, 'waltz': length}.get(style, 1)
        scale = length / song.beats if style not in ('whole', 'waltz') else 1
        for t, m in pat:
            if t * scale >= length - 1e-6 and style not in ('whole', 'waltz'): continue
            song.note(start + t * scale if style not in ('whole', 'waltz') else start, min(step, length), m, kind=kind,
                      duty=duty, gain=gain, a=.004, d=.05, s=.85, r=.04, legato=.85)
    return f


def arp_fn(song, pattern=(0, 1, 2, 1), step=.25, octave=4, kind='pulse', duty=.125, gain=.07, pan=.3, r=.04, s=.4):
    def f(start, length, ch):
        root, iv, _ = ch
        notes = [12 * (octave + 1) + root + i for i in iv[:3]]
        notes += [notes[0] + 12]
        n = int(round(length / step))
        for k in range(n):
            idx = pattern[k % len(pattern)]
            song.note(start + k * step, step, notes[idx % len(notes)], kind=kind, duty=duty, gain=gain, pan=pan,
                      a=.002, d=.05, s=s, r=r, legato=.7)
    return f


def pad_fn(song, octave=4, kind='tri', gain=.06, pan=-.2, every=None):
    def f(start, length, ch):
        root, iv, _ = ch
        for i in iv[:3]:
            song.note(start, length, 12 * (octave + 1) + root + i, kind=kind, gain=gain, pan=pan, a=.08, d=.3, s=.7,
                      r=.2, legato=.98)
    return f


def stab_fn(song, beats_on=(1, 3), octave=4, kind='pulse', duty=.25, gain=.06, pan=-.25, dur=.4):
    """뒷박 코드 (오프비트 반주)"""
    def f(start, length, ch):
        root, iv, _ = ch
        for b in beats_on:
            if b >= length: continue
            for i in iv[:3]:
                song.note(start + b, dur, 12 * (octave + 1) + root + i, kind=kind, duty=duty, gain=gain, pan=pan,
                          a=.002, d=.06, s=.5, r=.05, legato=.8)
    return f
