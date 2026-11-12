"""EvoTail BGM 전곡. python songs.py [곡이름...] → out/<곡>.ogg (+ .mp3 미리듣기)
모든 곡은 이 저장소에서 새로 작곡한 오리지널 (코드 진행 + 손으로 쓴 멜로디)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # chip.py·song_map_day.py
from chip import *
import song_map_day

SONGS = {}


def song(fn):
    SONGS[fn.__name__] = fn
    return fn


def map_day(out): return song_map_day.build(out)
SONGS['map_day'] = map_day


@song
def map_night(out):
    """지도(밤): 낮 마을 멜로디를 느리고 잔잔하게. 오르골 + 따뜻한 패드, 북 없이 브러시만."""
    s = Song('map_night', 78, 16)
    prog = ['Cmaj7', 'G6', 'Am7', 'Fmaj7', 'Cmaj7', 'G6', 'Fmaj7', 'G', 'Fmaj7', 'G6', 'Em7', 'Am7', 'Fmaj7', 'G', 'C', 'C G7']
    s.chords(prog, pad_fn(s, 4, 'tri', gain=.05, pan=-.25))
    s.chords(prog, bass_fn(s, 'half', 2, gain=.28))
    s.chords(prog, arp_fn(s, (0, 1, 2, 3, 2, 1), .5, 5, kind='sine', gain=.035, pan=.4, r=.4, s=.2))
    s.melody(song_map_day.A + ' ' + song_map_day.B, 0, kind='tri', gain=.2, pan=0, a=.01, d=.2, s=.5, r=.25, vib=.006)
    s.melody(song_map_day.A + ' ' + song_map_day.B, 0, kind='sine', gain=.05, octave=1, a=.002, d=.25, s=.1, r=.3, pan=.3)
    s.drums({'b': '....x.......x...'}, gains={'b': .1})
    return s.finish(out, echo=(.75, .3), lp=6000)


@song
def home(out):
    """집·주방: 포근한 3박자 왈츠. G장조 132bpm."""
    A = """D5:1 G5:1 B5:1 | A5:2 F#5:1 | G5:1 E5:1 B4:1 | C5:2 E5:1
D5:1 B4:1 G4:1 | A4:1 C5:1 F#5:1 | G5:1.5 A5:.5 B5:1 | G5:2 r:1"""
    B = """E5:1 G5:1 C6:1 | B5:2 G5:1 | C6:1 A5:1 E5:1 | F#5:2 D5:1
B5:1 G5:1 E5:1 | C6:1 E5:1 G5:1 | F#5:1 A5:1 C6:1 | B5:1.5 A5:.5 G5:1"""
    prog = ['G', 'D/F#', 'Em', 'C', 'G', 'Am D', 'G', 'G', 'C', 'G', 'Am', 'D', 'Em', 'C', 'D7', 'G']
    s = Song('home', 132, 32, beats=3)
    s.chords(prog * 2, bass_fn(s, 'waltz', 2, gain=.32))
    s.chords(prog * 2, stab_fn(s, (1, 2), 4, duty=.5, gain=.035, pan=-.25, dur=.5))
    lead = dict(kind='pulse', duty=.5, gain=.13, a=.01, d=.1, s=.6, r=.1, vib=.005, detune=.004)
    x = s.melody(A + ' ' + B, 0, **lead)
    s.melody(A + ' ' + B, x, **lead)
    s.melody(A + ' ' + B, x, kind='tri', gain=.06, octave=-1, pan=.3, a=.01, s=.6)        # 두 번째 바퀴 아래 화음
    s.drums({'b': 'x...x...x...'}, gains={'b': .1})
    return s.finish(out, echo=(.5, .2), lp=7000)


@song
def shop(out):
    """상점: 통통 튀는 스윙. D장조 124bpm."""
    A = """F#5:.5 A5:.5 r:.5 A5:.5 B5:.5 A5:.5 F#5:1 | D5:.5 F#5:.5 r:.5 F#5:.5 E5:.5 D5:.5 B4:1
G4:.5 B4:.5 D5:.5 G5:.5 F#5:.5 G5:.5 B5:1 | A5:1.5 G5:.5 E5:1 C#5:1
F#5:.5 A5:.5 r:.5 A5:.5 B5:.5 A5:.5 D6:1 | C#6:.5 B5:.5 A5:.5 F#5:.5 D5:1 B4:1
E5:.5 G5:.5 B5:1 A5:.5 G5:.5 E5:.5 C#5:.5 | D5:2 r:2"""
    B = """B5:1 B5:.5 A5:.5 G5:1 D5:1 | C#5:.5 E5:.5 A5:1 G5:.5 F#5:.5 E5:1
F#5:1 A5:1 C#6:1 A5:1 | B5:1.5 A5:.5 F#5:1 D5:1
G5:.5 A5:.5 B5:.5 D6:.5 B5:1 G5:1 | A5:.5 B5:.5 C#6:.5 E6:.5 C#6:1 A5:1
D6:1 A5:.5 F#5:.5 B5:1 F#5:1 | G5:1 E5:1 C#5:1 A4:1"""
    prog = ['D', 'Bm', 'G', 'A7', 'D', 'Bm', 'Em A7', 'D', 'G', 'A', 'F#m', 'Bm', 'G', 'A', 'D Bm', 'Em A7']
    s = Song('shop', 124, 32, swing=.33)
    s.chords(prog * 2, bass_fn(s, 'walk', 2, gain=.34))
    s.chords(prog * 2, stab_fn(s, (1, 3), 4, duty=.25, gain=.04, pan=-.3, dur=.3))
    lead = dict(kind='pulse', duty=.125, gain=.15, a=.003, d=.06, s=.5, r=.06)
    x = s.melody(A + ' ' + B, 0, **lead)
    s.melody(A + ' ' + B, x, kind='pulse', duty=.25, gain=.14, a=.003, d=.06, s=.5, r=.06)
    s.melody(A + ' ' + B, x, kind='sine', gain=.05, octave=1, pan=.35, a=.002, d=.1, s=.2, r=.12)
    s.drums({'k': 'x.......x.......', 's': '....x.......x...', 'h': 'x.x.x.x.x.x.x.x.'})
    return s.finish(out, echo=(.5, .18))


@song
def hospital(out):
    """병원: 부드럽고 차분하게. C장조 76bpm, 북 없음."""
    M = """E5:2 G5:1 E5:1 | C5:3 r:1 | A4:1 C5:1 F5:1.5 E5:.5 | D5:3 r:1
E5:2 G5:1 C6:1 | B5:1 A5:2 r:1 | F5:1 E5:1 D5:1 C5:1 | B4:3 r:1
C6:2 A5:1 F5:1 | B5:2 G5:1 D5:1 | E5:1 G5:1 B5:2 | A5:3 r:1
F5:1 A5:1 C6:1.5 B5:.5 | A5:1 G5:1 D5:2 | E5:2 D5:1 E5:1 | C5:3 r:1"""
    prog = ['C', 'Am', 'F', 'G', 'C', 'Am', 'Dm7', 'G', 'Fmaj7', 'G', 'Em7', 'Am', 'F', 'G', 'C', 'C']
    s = Song('hospital', 76, 32)
    s.chords(prog * 2, pad_fn(s, 3, 'tri', gain=.06, pan=-.2))
    s.chords(prog * 2, bass_fn(s, 'whole', 2, gain=.25))
    s.chords(prog * 2, arp_fn(s, (0, 1, 2, 3, 2, 1, 0, 2), .5, 5, kind='sine', gain=.035, pan=.35, r=.5, s=.15))
    x = s.melody(M, 0, kind='sine', gain=.24, a=.03, d=.3, s=.6, r=.3, vib=.006)
    s.melody(M, x, kind='tri', gain=.18, a=.03, d=.3, s=.6, r=.3, vib=.006)
    s.melody(M, x, kind='sine', gain=.06, octave=-1, pan=-.3, a=.05, s=.6, r=.3)
    return s.finish(out, echo=(1.0, .3), lp=5000, rms=.12)


@song
def farm(out):
    """밭: 시골 들판. G장조 100bpm, 밴조 같은 뜯는 소리 + 휘파람 멜로디."""
    A = """D5:.5 E5:.5 G5:1 G5:.5 A5:.5 B5:1 | A5:.5 G5:.5 E5:.5 D5:.5 G5:2
E5:.5 G5:.5 C6:1 B5:.5 A5:.5 G5:1 | D5:1 B4:1 D5:2
D5:.5 E5:.5 G5:1 G5:.5 A5:.5 B5:1 | B5:.5 D6:.5 B5:.5 A5:.5 G5:1 E5:1
E5:.5 F#5:.5 G5:.5 A5:.5 C#6:1 A5:1 | D6:1.5 C6:.5 A5:1 F#5:1"""
    B = """E6:1 D6:.5 C6:.5 G5:1 E5:1 | D6:1 B5:.5 A5:.5 G5:2
F#5:.5 A5:.5 D6:1 C6:.5 A5:.5 F#5:1 | G5:1 B5:1 D6:2
E6:.5 D6:.5 C6:.5 B5:.5 A5:1 G5:1 | B5:.5 A5:.5 G5:.5 E5:.5 D5:2
C5:.5 D5:.5 F#5:.5 A5:.5 C6:1 F#5:1 | G5:2 r:2"""
    prog = ['G', 'G', 'C', 'G', 'G', 'Em', 'A7', 'D7', 'C', 'G', 'D', 'G', 'C', 'G', 'D7', 'G']
    s = Song('farm', 100, 32)
    s.chords(prog * 2, bass_fn(s, 'half', 2, gain=.34))
    s.chords(prog * 2, arp_fn(s, (0, 2, 1, 2, 3, 2, 1, 2), .5, 4, duty=.125, gain=.06, pan=.3, r=.03, s=.15))
    whistle = dict(kind='tri', gain=.22, a=.02, d=.1, s=.7, r=.08, vib=.008)
    x = s.melody(A + ' ' + B, 0, **whistle)
    s.melody(A + ' ' + B, x, kind='pulse', duty=.5, gain=.12, a=.004, d=.08, s=.5, r=.06)
    s.drums({'k': 'x.......x.......', 'b': '....x.......x...', 'h': '..x...x...x...x.'}, gains={'k': .45, 'b': .18, 'h': .08})
    return s.finish(out, echo=(.5, .2), lp=8000)


@song
def hunt(out):
    """사냥터: 모험. E단조 132bpm, 말발굽 리듬."""
    A = """E5:1 B4:.5 E5:.5 G5:1 F#5:.5 E5:.5 | G5:1.5 A5:.5 G5:1 E5:1
F#5:1 D5:.5 F#5:.5 A5:1 G5:.5 F#5:.5 | E5:3 r:1
E5:1 B4:.5 E5:.5 G5:1 A5:.5 B5:.5 | C6:1.5 B5:.5 A5:1 G5:1
A5:1 F#5:.5 D5:.5 F#5:1 A5:1 | B5:2 D#5:2"""
    B = """E5:.5 G5:.5 C6:1 B5:.5 A5:.5 G5:1 | F#5:.5 A5:.5 D6:1 C6:.5 B5:.5 A5:1
B5:1 F#5:1 D5:1 F#5:1 | G5:1.5 F#5:.5 E5:2
E6:1 C6:.5 G5:.5 E6:1 D6:1 | D6:1 A5:.5 F#5:.5 D6:1 C6:1
C6:1 A5:.5 E5:.5 A5:1 B5:1 | B5:2 F#5:1 D#5:1"""
    prog = ['Em', 'C', 'D', 'Em', 'Em', 'C', 'D', 'B7', 'C', 'D', 'Bm', 'Em', 'C', 'D', 'Am', 'B7']
    s = Song('hunt', 132, 32)
    s.chords(prog * 2, bass_fn(s, 'drive', 2, kind='pulse', duty=.5, gain=.16))
    s.chords(prog * 2, bass_fn(s, 'rootfifth', 1, gain=.3))
    s.chords(prog * 2, arp_fn(s, (0, 1, 2, 1), .25, 4, duty=.125, gain=.04, pan=.35))
    lead = dict(kind='pulse', duty=.25, gain=.15, a=.003, d=.08, s=.6, r=.06, vib=.004)
    x = s.melody(A + ' ' + B, 0, **lead)
    s.melody(A + ' ' + B, x, **lead)
    s.melody(B, x + 32, kind='pulse', duty=.5, gain=.07, octave=-1, pan=-.35)      # 두 번째 B는 두 겹
    s.drums({'k': 'x..x..x.x..x..x.', 's': '....x.......x...', 'h': 'x.x.x.x.x.x.x.x.'})
    for b in (0, 16): s.drum('c', b * 4, .2)
    return s.finish(out)


@song
def arena(out):
    """전투장(스테이지 고르기·출전 준비): 행진곡. F장조 112bpm, 나팔 + 작은북."""
    A = """C5:.5 C5:.25 C5:.25 F5:1 A5:1 F5:1 | D6:1.5 C6:.5 Bb5:1 F5:1
G5:.5 G5:.25 G5:.25 C6:1 E5:1 G5:1 | F5:2 C5:2
D5:.5 F5:.5 A5:1 D6:1 A5:1 | Bb5:1 D6:1 F6:1 D6:1
E6:1.5 D6:.5 C6:1 Bb5:1 | Bb5:1 G5:1 E5:1 C5:1"""
    B = """D6:1 Bb5:.5 F5:.5 Bb5:1 D6:1 | C6:1.5 A5:.5 F5:2
E5:.5 G5:.5 C6:1 E6:1 C6:1 | A5:2 F5:2
F5:.5 Bb5:.5 D6:1 F6:1 D6:1 | C6:1 A5:1 F5:1 A5:1
Bb5:1 G5:1 C6:1 E5:1 | F5:2 r:1 C5:1"""
    prog = ['F', 'Bb', 'C', 'F', 'Dm', 'Bb', 'C', 'C7', 'Bb', 'F', 'C', 'F', 'Bb', 'F', 'Gm C7', 'F']
    s = Song('arena', 112, 32)
    s.chords(prog * 2, bass_fn(s, 'rootfifth', 2, gain=.34))
    s.chords(prog * 2, stab_fn(s, (1, 3), 4, duty=.5, gain=.04, pan=-.3, dur=.35))
    brass = dict(kind='pulse', duty=.5, gain=.12, a=.015, d=.1, s=.7, r=.06, detune=.006, vib=.004)
    x = s.melody(A + ' ' + B, 0, **brass)
    s.melody(A + ' ' + B, x, **brass)
    s.melody(A + ' ' + B, x, kind='pulse', duty=.25, gain=.06, octave=-1, pan=.35, a=.01, s=.7)
    s.drums({'k': 'x.......x.......', 's': '..x.x...x.x.xxxx', 'h': ''}, gains={'k': .5, 's': .22})
    for b in (0, 16): s.drum('c', b * 4, .2)
    return s.finish(out, echo=(.5, .18))


@song
def battle(out):
    """전투: 빠르고 긴장감. A단조 150bpm."""
    A = """A5:.5 A5:.5 E5:.5 A5:.5 C6:1 B5:1 | A5:.5 A5:.5 F5:.5 A5:.5 C6:1 D6:1
B5:.5 B5:.5 G5:.5 B5:.5 D6:1 C6:.5 B5:.5 | A5:2 E5:2
A5:.5 C6:.5 E6:1 D6:.5 C6:.5 B5:1 | C6:.5 A5:.5 F5:1 A5:.5 C6:.5 F6:1
D6:1 B5:1 G5:1 D6:1 | B5:2 G#5:2"""
    B = """C6:1.5 A5:.5 F5:1 C6:1 | D6:1.5 B5:.5 G5:1 D6:1
E6:1 B5:.5 G5:.5 E5:1 G5:1 | A5:1 C6:1 E6:2
F6:1 E6:.5 D6:.5 C6:1 A5:1 | B5:1 D6:.5 B5:.5 G5:1 B5:1
G#5:.5 B5:.5 E6:1 D6:.5 B5:.5 G#5:1 | E5:.5 G#5:.5 B5:.5 D6:.5 E6:2"""
    prog = ['Am', 'F', 'G', 'Am', 'Am', 'F', 'G', 'E', 'F', 'G', 'Em', 'Am', 'F', 'G', 'E', 'E7']
    s = Song('battle', 150, 32)
    s.chords(prog * 2, bass_fn(s, 'bounce', 2, kind='pulse', duty=.5, gain=.15))
    s.chords(prog * 2, bass_fn(s, 'drive', 1, gain=.3))
    s.chords(prog * 2, arp_fn(s, (0, 1, 2, 3), .25, 4, duty=.125, gain=.045, pan=.35))
    lead = dict(kind='pulse', duty=.25, gain=.15, a=.002, d=.07, s=.65, r=.05, vib=.003)
    x = s.melody(A + ' ' + B, 0, **lead)
    s.melody(A + ' ' + B, x, **lead)
    s.melody(A + ' ' + B, x, kind='pulse', duty=.5, gain=.07, octave=-1, pan=-.35, a=.002, s=.6)
    s.drums({'k': 'x.....x.x.......', 's': '....x.......x...', 'h': 'x.x.x.x.x.x.x.x.'})
    s.drums({'k': 'x.....x.x.x.....', 's': '....x.......x.xx', 'o': '..............x.'}, start=64, bars=16)
    for b in (0, 8, 16, 24): s.drum('c', b * 4, .2)
    return s.finish(out)


# ---------- 짧은 효과음악 (반복 안 함) ----------
@song
def jingle_win(out):
    s = Song('jingle_win', 140, 3)
    s.melody('C5:.5 E5:.5 G5:.5 C6:1.5 r:.5 A5:.5 B5:.5 C6:2.5 r:3', 0, kind='pulse', duty=.5, gain=.16, detune=.006, s=.7, r=.2)
    s.melody('E4:.5 G4:.5 B4:.5 E5:1.5 r:.5 F4:.5 G4:.5 E5:2.5', 0, kind='pulse', duty=.25, gain=.08, s=.7, r=.2)
    s.melody('C3:2 r:1 F2:1 G2:1 C3:2.5', 0, kind='tri', gain=.3)
    s.drum('k', 0, .5); s.drum('c', 0, .2); s.drum('s', 3.5, .3); s.drum('s', 3.75, .3); s.drum('c', 4, .25); s.drum('k', 4, .5)
    return s.finish(out, loop=False, echo=(.5, .2))


@song
def jingle_lose(out):
    s = Song('jingle_lose', 92, 3)
    s.melody('E5:1 D#5:1 D5:1 C#5:3 r:2', 0, kind='pulse', duty=.25, gain=.15, vib=.012, s=.7, r=.3)
    s.melody('A3:3 A2:3', 0, kind='tri', gain=.28, s=.8, r=.4)
    return s.finish(out, loop=False, echo=(.75, .25), lp=6000)


@song
def jingle_hatch(out):
    s = Song('jingle_hatch', 150, 3)
    s.melody('C6:.25 E6:.25 G6:.25 C7:.25 E6:.25 G6:.25 C7:.25 E7:.25 r:.5 G6:.5 C7:2 r:2', 0, kind='sine', gain=.16, a=.002,
             d=.2, s=.2, r=.3)
    s.melody('C5:1 G5:1 [C5+E5+G5+C6]:3', 0, kind='pulse', duty=.5, gain=.06, detune=.006, a=.02, s=.7, r=.3)
    s.drum('c', 2, .15)
    return s.finish(out, loop=False, echo=(.5, .3))


if __name__ == '__main__':
    # python tools/bgm/songs.py [곡이름...] (어느 폴더에서나). numpy + ffmpeg 필요
    # 중간 파일(wav·mp3 미리듣기)은 tools/bgm/out/, 게임이 쓰는 .ogg만 assets/bgm/으로 복사
    import os, shutil
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, 'out')
    bgm_dir = os.path.join(os.path.dirname(os.path.dirname(here)), 'assets', 'bgm')
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(bgm_dir, exist_ok=True)
    names = sys.argv[1:] or list(SONGS)
    for n in names:
        ogg = os.path.join(out_dir, f'{n}.ogg')
        print(n, round(SONGS[n](ogg), 1), 's')
        shutil.copy(ogg, os.path.join(bgm_dir, f'{n}.ogg'))
