"""지도(낮): 밝고 통통 튀는 섬 마을 곡. C장조 116bpm, 32마디(A B A' B')."""
from chip import *

A = """C5:.5 E5:.5 G5:1 E5:.5 G5:.5 C6:1
B5:1 G5:1 D5:1.5 r:.5
A4:.5 C5:.5 E5:1 C5:.5 E5:.5 A5:1
G5:.5 F5:.5 E5:.5 D5:.5 C5:1 r:1
E5:.5 E5:.5 G5:1 G5:.5 A5:.5 G5:1
F5:.5 E5:.5 D5:1 B4:1 G4:1
A4:.5 C5:.5 F5:1 E5:.5 D5:.5 C5:1
D5:1 E5:.5 D5:.5 B4:1 r:1"""
B = """A5:1.5 G5:.5 F5:1 A5:1
G5:1.5 F5:.5 E5:1 D5:1
E5:1 G5:1 B5:1.5 A5:.5
C6:1 B5:.5 A5:.5 E5:2
F5:.5 G5:.5 A5:1 C6:1 A5:1
B5:.5 A5:.5 G5:1 D5:1 B4:1
C5:.5 E5:.5 G5:.5 C6:.5 E6:1 D6:.5 B5:.5
C6:2 r:1 G4:.5 B4:.5"""
CH_A = ['C', 'G', 'Am', 'F', 'C', 'G', 'F', 'G']
CH_B = ['F', 'G', 'Em', 'Am', 'F', 'G', 'C', 'C G7']


def build(out):
    s = Song('map_day', 116, 32)
    prog = CH_A + CH_B + CH_A + CH_B
    s.chords(prog, bass_fn(s, 'rootfifth', 2, gain=.36))
    s.chords(prog, arp_fn(s, (0, 1, 2, 3, 2, 1, 0, 1), .25, 4, duty=.125, gain=.045, pan=.35))
    s.chords(prog, stab_fn(s, (1, 3), 4, duty=.25, gain=.035, pan=-.3, dur=.35))
    lead = dict(kind='pulse', duty=.25, gain=.16, pan=-.05, a=.004, d=.08, s=.55, r=.08, vib=.004)
    x = s.melody(A + ' ' + B, 0, **lead)
    s.melody(A + ' ' + B, x, **lead)
    # 두 번째 바퀴: 한 옥타브 위 반짝이 (오르골 느낌)
    s.melody(A + ' ' + B, x, kind='tri', gain=.07, pan=.4, octave=1, a=.002, d=.12, s=.25, r=.15)
    beat = {'k': 'x.......x.......', 's': '....x.......x...', 'h': '..x...x...x...x.', 'b': 'x.x.x.x.x.x.x.x.'}
    s.drums(beat, start=0, bars=32)
    for b in (0, 16): s.drum('c', b * 4, .18)
    for b in (7, 15, 23, 31):                      # 마디 끝 필
        for i, k in enumerate('tt.s'):
            if k != '.': s.drum(k, b * 4 + 3 + i * .25, .3)
    return s.finish(out)


if __name__ == '__main__':
    import sys
    print(build(sys.argv[1] if len(sys.argv) > 1 else 'out/map_day.ogg'))
