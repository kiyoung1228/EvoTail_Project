"""글씨 넘침 점검: 칸 안 글씨(widgets.text_in / record)가 칸 안쪽에 사방 2px(TEXT_PAD) 이상 여백을 두는지.

실제 창을 임시 세이브로 띄워 지도·내 동물(모든 동물)·준비 중·설정·확인·도움말·집 주방·전투장 화면을 돌며 기록을 모은다.
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
from gui.scenes.home_kitchen import LIST_ROWS as LIST_ROWS_KITCHEN

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
        s['inventory']['battle_bandage'] = 12                 # 전투 아이템 목록 (두 자리 개수)
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
        self.open_overlay(ConfirmOverlay(self, '불러올까?', '마지막으로 저장된 상태를 다시 불러옴', '불러오기', 'purple',
                                         lambda: None)); frames(2)
        self.close_overlay(); self.open_overlay(HelpOverlay(self)); frames(2)
        self.close_overlay(); self.close_overlay(); frames(1)
        # 집·주방: 레시피(모든 레시피, 재료 있음·부족) → 미니게임 → 결과 4종 → 음식 주기(모든 요리)
        def kitchen_fixture(s):    # test fixture only (temp save)
            for item in ('egg_food', 'potato', 'salt', 'onion', 'tomato', 'milk', 'butter', 'wheat', 'chicken',
                         'beef', 'rice', 'lucky_rabbit'):
                s['inventory'][item] = 3
            s['inventory'].update(egg_food=9, food_perfect_rabbit_stew=1, food_omelette_rice=12, burned_food=2)
            s['cook_xp'] = 90
            return True
        g._mutate(kitchen_fixture); self.refresh()
        self.go('home'); frames(2)
        ks = self.scene
        for key in ks.recipes:
            ks.recipe = key; frames(1)
            move(ks.cell_rect(list(ks.recipes).index(key)).center)
        self.act('cook', None, recipe='fried_chicken', judgment='good')       # 닭고기 부족 상태도
        ks.enter(); ks.recipe = 'fried_chicken'; frames(2)
        ks.recipe = 'chicken_burger'; frames(2)
        shot('real_kitchen.png')
        ks.start_cooking('boiled_egg'); frames(10)
        orig = g.rng.random
        for judgment, rnd in (('perfect', None), ('good', None), ('miss', 0.0), ('miss', 0.99)):
            if ks.mode != 'cook':
                ks.start_cooking('boiled_egg'); frames(2)
            if rnd is not None:
                g.rng.random = lambda: rnd
            ks._judge(judgment); frames(2)
            g.rng.random = orig
            frames(30)
        shot('real_kitchen_result.png')
        ks.feed_result(); frames(2)
        for item in ks.dishes():
            ks.dish = item; frames(1)
            move(ks.cell_rect(ks.dishes().index(item)).center)
        for a in self.state['animals'][:LIST_ROWS_KITCHEN]:
            ks.target = a['id']; frames(1)
        ks.scroll = max(0, len(self.state['animals']) - LIST_ROWS_KITCHEN); frames(2)
        shot('real_kitchen_feed.png')
        # 상점: 탭 6개(모든 상품) → 부화(새/중복) → 병원(환자 있음/없음, 성공/실패) → 장비 고르기
        def shop_fixture(s):    # test fixture only (temp save)
            s['inventory'].update(heal_basic=2, heal_advanced=1, egg_special=3, egg_basic=1, equip_claw=1,
                                  equip_shell=2, potion_attack=1)
            for k in ('dealer_normal_01', 'healer_special_05'):
                s['animals'][k]['sick'] = True
            return True
        g._mutate(shop_fixture); self.refresh()
        self.go('shop'); frames(2)
        sh = self.scene
        for tid, *_ in __import__('gui.items', fromlist=['TABS']).TABS:
            sh.go_tab(tid); frames(1)
            for _ in range(4):
                for item in sh.visible():
                    sh.selected[tid] = item; frames(1)
                    move(sh.cell_rect(sh.visible().index(item)).center)
                sh.scroll += 3; frames(1)
            sh.scroll = 0
        sh.go_tab('egg'); sh.selected['egg'] = 'egg_special'; frames(1)
        shot('real_shop.png')
        orig_rng = g.rng.random
        g.rng.random = lambda: 0.5
        sh.hatch(); self.overlays[-1].skip(); frames(2)
        key = self.overlays[-1].result['id']
        shot('real_hatch.png')
        self.close_overlay()
        orig_choice = g.rng.choice
        g.rng.choice = lambda opts: key
        sh.hatch(); self.overlays[-1].skip(); frames(2)            # 중복
        g.rng.choice = orig_choice
        self.close_overlay()
        sh.selected['egg'] = 'egg_basic'
        sh.hatch(); self.overlays[-1].skip(); frames(2)            # 남은 알 0개 (한 번 더 꺼짐)
        g.rng.random = orig_rng
        self.close_overlay(); frames(1)
        self.go('hospital'); frames(2)
        hs = self.scene
        for a in hs.patients():
            hs.selected = a['id']; frames(1)
        shot('real_hospital.png')
        g.rng.random = lambda: 0.99
        hs.potion = 'heal_basic'; hs.treat(); frames(2); self.close_overlay()
        g.rng.random = lambda: 0.0
        hs.potion = 'heal_basic'; hs.treat(); frames(2); self.close_overlay()
        hs.potion = 'heal_advanced'; hs.treat(); frames(2); self.close_overlay()
        g.rng.random = orig_rng
        frames(2)
        self.go('animals', selected='dealer_normal_01'); frames(2)
        from gui.scenes.animals_scene import EquipOverlay
        self.open_overlay(EquipOverlay(self, 'dealer_normal_01')); frames(2)
        self.overlays[-1]._equip('equip_claw'); frames(2)
        self.open_overlay(EquipOverlay(self, 'dealer_normal_01')); frames(2)
        self.close_overlay(); frames(2)
        # 밭: 빈 밭(씨앗 있음/0개) / 자라는 중 / 다 자람 / 넓힐 칸 / 잠긴 칸 / 넓히기 확인 창 / 모두 수확
        def farm_fixture(s):    # test fixture only (temp save)
            v = s['clock']['virtual']
            s['inventory'].update(seed_potato=12, seed_cabbage=3)
            s['plots'] = [{'crop': 'tomato', 'end': v - 1, 'ready': True},
                          {'crop': 'cabbage', 'end': v + 252, 'ready': False},
                          {'crop': None, 'end': None, 'ready': False}]
            return True
        g._mutate(farm_fixture); self.refresh()
        self.go('farm'); frames(2)
        fm = self.scene
        for i in range(6):
            fm.selected = i; frames(1)
            if i == 2:
                for c in fm.crops():
                    fm.seed = c; frames(1)
        shot('real_farm.png')
        fm.selected = 3; frames(1); fm.ask_expand(); frames(2); self.close_overlay()
        fm.harvest_all(); frames(2)
        g._mutate(lambda s: s['inventory'].update(seed_potato=0, seed_cabbage=0) or True); self.refresh()
        fm.selected = 2; frames(2)
        # 사냥터: 빈 사냥터(보낼 동물 목록·휠) / 사냥 중 / 완료(말풍선) / 불러오기 확인 창 / 보낼 동물 없음
        def hunt_fixture(s):    # test fixture only (temp save)
            v = s['clock']['virtual']
            s['animals']['dealer_normal_01']['activity'] = {'kind': 'hunt', 'area': 'chicken_coop',
                                                            'start': v - 100, 'end': v + 760}
            s['hunts'] = {'chicken_coop': {'animal': 'dealer_normal_01', 'end': v + 760, 'ready': False},
                          'pig_pen': {'animal': 'healer_special_05', 'end': v - 1, 'ready': True}}
            return True
        g._mutate(hunt_fixture); self.refresh()
        self.go('hunting'); frames(2)
        hu = self.scene
        for area in list(hu.areas):
            hu.selected = area; frames(1)
            for k in range(0, len(self.state['animals']), 3):
                hu.scroll = k; frames(1)
            hu.scroll = 0
        shot('real_hunt.png')
        # 달토끼 언덕(이름이 가장 긴 고기): 사냥 중 / 완료 (가방 보유 두 자리)
        def rabbit(ready):
            def fn(s):
                v = s['clock']['virtual']
                s['inventory']['lucky_rabbit'] = 10
                s['hunts']['rabbit_hill'] = {'animal': 'tank_special_05', 'end': v + (-1 if ready else 3000),
                                             'ready': ready}
                return True
            return fn
        for ready in (False, True):
            g._mutate(rabbit(ready)); self.refresh()
            hu.selected = 'rabbit_hill'; frames(2)
        hu.selected = 'chicken_coop'; frames(1); hu.ask_recall(); frames(2); self.close_overlay()
        def no_one(s):          # 보낼 동물 없음
            for a in s['animals'].values():
                a['fatigue'] = 100
            return True
        g._mutate(no_one); self.refresh()
        hu.selected = 'ranch'; frames(2)
        def rested(s):          # 뒤의 전투장 점검을 위해 되돌림
            for a in s['animals'].values():
                a['fatigue'] = 0
                a['activity'] = None
            s['hunts'] = {}
            return True
        g._mutate(rested); self.refresh()
        # 전투장: 스테이지 고르기(모든 단계) → 출전 준비 → 전투(대상 고르기·기록 펼침) → 결과
        self.go('battle'); frames(2)
        sp = self.scene
        for st in sp.stages:
            sp.selected = st['id']; frames(1)
        sp.selected = sp.stages[0]['id']; frames(1)
        self.go('battle_prep', stage_id=sp.selected); frames(2)
        tp = self.scene
        ready = [a['id'] for a in self.state['animals'] if a.get('participation')][:3]
        tp.team = ready; frames(2)
        for k in range(len(tp._potion_keys())):
            tp.cycle_potion(tp._potion_keys()[k]); frames(1)
        shot('real_prep.png')
        if len(ready) == 3:
            tp.start(); frames(3)
            bs = self.scene
            for f in bs.view['player']:
                bs.selected = f['id']; bs._load_actions(); frames(2)
                if any(a['kind'] == 'attack' and a['target'] for a in bs.actions):
                    bs.mode = 'attack'; frames(2); bs.mode = None
            bs.item_menu = True; frames(2)                     # 전투 아이템 목록
            bs.item_menu = False
            move((550, 320)); frames(2)
            shot('real_battle.png')
            res = self.call('forfeit_battle'); self.refresh()
            self.go('battle_result', result=res, before={k: 0 for k in ready}); frames(2)
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
