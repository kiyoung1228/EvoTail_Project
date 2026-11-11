"""글씨 넘침 점검: 칸 안 글씨(widgets.text_in / record)가 칸 안쪽에 사방 2px(TEXT_PAD) 이상 여백을 두는지.

실제 창을 임시 세이브로 띄워 지도·내 동물(모든 동물)·준비 중·설정·확인·도움말 화면을 돌며 기록을 모은다.
    python tools/check_text_fit.py            # 검사만
    python tools/check_text_fit.py shots      # + 실제 창 크기 스크린샷 (saves/screenshots/, 깃 제외)
위반이 있으면 종료 코드 1. 넘치면 글자를 줄이지 말고 칸을 넓힌다.
"""
import os, sys, tempfile
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ); os.chdir(PROJ)
SHOTS = 'shots' in sys.argv
OUT = os.path.join(PROJ, 'saves', 'screenshots')
if SHOTS:
    os.makedirs(OUT, exist_ok=True)
import pygame
import run_gui
from gui.app import App
from gui import theme as T
from gui import widgets as W
from gui.scenes.settings import SettingsOverlay, ConfirmOverlay, HelpOverlay

save = os.path.join(tempfile.mkdtemp(), 'layout.db')


def scripted_run(self):
    g = self.game
    def setup(s):    # test fixture only (temp save): many animals, long names, evolved, sick, hungry
        for k in g.characters:
            if k not in s['animals']:
                s['animals'][k] = g._new_animal(k, s['clock']['virtual'])
        for k, a in s['animals'].items():
            if k.startswith('dealer_special'):
                a['stage'] = 3
        s['animals']['healer_normal_03']['sick'] = True
        s['animals']['tank_normal_02']['fullness'] = 10
        s['yard'] = ['dealer_special_02', 'tank_normal_02', 'healer_special_05']
        s['coins'] = 1234567
        return True
    g._mutate(setup)
    self.act('start_training', None, key='tank_normal_01', stat='defense', difficulty='easy')
    self.refresh()
    S = T.SCALE
    W.LAYOUT_LOG = []

    def frames(n=2):
        for _ in range(n):
            self.step(1 / T.FPS)
    def move(lpos):
        wpos = (lpos[0] * S + S // 2, lpos[1] * S + S // 2)
        pygame.mouse.set_pos(wpos)
        pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, pos=wpos, rel=(0, 0), buttons=(0, 0, 0)))
        frames(2)
    def shot(name):
        if SHOTS:
            pygame.image.save(self.window, os.path.join(OUT, name)); print('saved', name, self.window.get_size())
    m = self.scenes['map']
    try:
        print('window', self.window.get_size(), 'scale', S)
        # 지도: 간판·메뉴·툴팁·알림·+N
        self.go('map'); frames(5)
        for key in m.places:
            move(m.places[key]['rect'].center)
        for key, _, _ in __import__('gui.scenes.map_scene', fromlist=['MENU']).MENU:
            move(m.menu_rect(key).center)
        self.toast('행운 이벤트! 코인 +30', 'info', 'coin'); frames(2)
        move(m.places['shop']['rect'].center)
        shot('real_map.png')
        # 시연 모드 칩 (상단 바)
        self.toggle_speed(T.SPEED_DEMO); frames(2); self.toggle_speed(T.SPEED_DEMO); frames(2)
        # 내 동물: 모든 동물 선택
        self.go('animals'); frames(2)
        sc = self.scene
        for a in self.state['animals']:
            sc.selected = a['id']; sc.enter(); frames(2)
        sc.selected = 'dealer_special_02'; sc.enter(); frames(2)
        idx = [a['id'] for a in self.state['animals']].index('tank_normal_01')
        sc.scroll = 0; r = sc._card_rect(1)
        move((r.right - 9, r.bottom - 9))
        shot('real_animals.png')
        sc.selected = 'tank_normal_01'; frames(2)
        # 마당 가득
        self.act('set_yard_animals', None, keys=[a['id'] for a in self.state['animals'][:self.state['yard_max']]])
        sc.selected = self.state['animals'][-1]['id']; frames(2)
        # 준비 중 화면
        self.go('battle'); frames(2)
        # 설정 창들
        self.go('map'); frames(2)
        o = SettingsOverlay(self); self.open_overlay(o); frames(2)
        move(o.speed_fast.center)
        shot('real_settings.png')
        for r in (5, 60, 1):
            self.toggle_speed(r) if r != 1 else self.toggle_speed(self.state['clock']['rate']); frames(2)
        o.save(); frames(2)
        self.open_overlay(ConfirmOverlay(self, '불러올까요?', '마지막으로 저장된 상태를 다시 불러와요', '불러오기', 'purple',
                                         lambda: None)); frames(2)
        self.close_overlay(); self.open_overlay(HelpOverlay(self)); frames(2)
    finally:
        pygame.quit()
    # ---- 검사 ----
    seen, bad = set(), []
    for msg, drawn, box, tag in W.LAYOUT_LOG:
        key = (msg, tuple(drawn), tuple(box))
        if key in seen:
            continue
        seen.add(key)
        m_left, m_right = drawn.x - box.x, box.right - drawn.right
        m_top, m_bottom = drawn.y - box.y, box.bottom - drawn.bottom
        worst = min(m_left, m_right, m_top, m_bottom)
        if worst < W.TEXT_PAD:
            bad.append((tag, msg, (m_left, m_right, m_top, m_bottom), tuple(box)))
    print(f'checked {len(seen)} boxed labels · violations {len(bad)}')
    for tag, msg, margins, box in sorted(set(bad)):
        print(f'  [{tag}] {msg!r} margins L{margins[0]} R{margins[1]} T{margins[2]} B{margins[3]} box {box}')
    self.violations = len(bad)


App.run = scripted_run
_app = {}
_orig_init = App.__init__


def _keep(self, *a, **k):
    _orig_init(self, *a, **k)
    _app['app'] = self


App.__init__ = _keep
run_gui.main(save)
sys.exit(1 if getattr(_app.get('app'), 'violations', 0) else 0)
