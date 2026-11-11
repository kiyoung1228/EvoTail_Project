# EvoTail GUI (Pygame)

## 실행

```
pip install -r requirements.txt   # pygame-ce (예전 pygame이 있으면 먼저 pip uninstall pygame)
python run_gui.py
```

- **F5**: 빠르게(5배) 켜기/끄기. 평소 플레이용 (쉬운 훈련 2분, 하루 12분)
- **F12**: 시연 모드(60배) 켜기/끄기. 영상 촬영용 (쉬운 훈련 10초). 켜져 있으면 상단 바에 빨간 표시
- 세이브는 `saves/game.db`에 자동 저장돼요 (깃에는 안 올라가요)

## 구조

```
run_gui.py              화면 등록하고 실행
gui/
  app.py                메인 루프, 상단 바, 알림, 백엔드 연결, 월드 스레드 관리
  theme.py              색, 폰트, 한글 라벨, 상태 3단계 기준
  widgets.py            버튼, 게이지, 패널, 도트 이미지 캐시
  scenes/
    map_scene.py        메인 화면: 섬 마을 지도(낮·밤), 건물 간판, 오른쪽 메뉴, 마당 동물
    animals_scene.py    내 동물: 동물 목록·상세, 간식, 훈련, 진화 (메뉴 "내 동물")
    placeholder.py      아직 안 만든 화면 (집, 상점, 병원, 밭, 전투장, 사냥터, 도감, 가방, 마이룸, 설정)
```

### 규칙
- 게임 규칙은 전부 백엔드(`roc/`)에 있어요. 화면은 **`app.call('명령')`으로 읽고, `app.act('명령')`으로 바꾸기만** 해요. 명령 목록은 `roc/bridge.py`의 `ALLOWED_COMMANDS`.
- `app.act(...)`는 실패하면 백엔드가 준 이유를 알림으로 띄우고, 성공하면 최신 상태를 다시 읽어요.
- 이름과 이미지는 백엔드가 **현재 진화 단계 기준**으로 줘요 (`name`, `sprite`). 화면에서 단계별로 고를 필요 없어요.

### 멀티스레딩
- **메인 스레드**: Pygame 루프. 그리기와 입력만.
- **월드 스레드** (`roc/worker.py`의 `GameWorker`): 1초마다 게임 시간을 흘려보내고(자율행동, 훈련·사냥 완료, 날씨, 질병) 큐에 알림만 넣어요. 화면은 건드리지 않아요.
- 메인 루프가 매 프레임 큐를 확인해서 알림이 오면 상태를 다시 읽고, 새 이벤트를 알림으로 띄워요.
- 백엔드 상태 변경은 `GameService` 안에서 잠금으로 보호돼요.

## 새 화면 추가하는 법
1. `gui/scenes/`에 `Scene`을 상속한 클래스 만들기 (`handle` → `update` → `draw`)
2. `run_gui.py`에서 `PlaceholderScene` 대신 등록
3. 지도 건물은 `map_scene.py`의 `PLACES`(키 = `assets/map/map.json`의 `places`), 오른쪽 메뉴는 `MENU`에 화면 이름이 이미 연결돼 있어요

## 화면 키트
모든 화면은 [docs/UI_KIT.md](docs/UI_KIT.md)를 따라요. 640×360 논리 화면에 그리고 창에 2배로 붙여요(좌표·마우스 전부 논리 픽셀).
위젯은 `gui/widgets.py`: `panel`, `card`, `ribbon`, `chip`, `gauge`, `Button`, `icon`, `SpriteCache`.

## 폰트
갈무리 도트 글꼴(`assets/fonts/`, OFL). `T.font('title' | 'body' | 'small' | 'big')`만 써요. 파일이 없으면 시스템 한글 폰트로 대신해요.
