# EvoTail 프로젝트 안내 (Claude용)

2026 기초프로젝트 레벨3 조별과제. Python + Pygame으로 만드는 **동물 육성·턴제 전투 게임**.
이 파일은 지금까지 팀에서 정한 내용과 코드 규칙을 정리한 것. 작업 전에 꼭 읽고 따를 것.

## 팀과 역할 (2명)
- **재은** (GitHub `emddl457`): GUI (`gui/`, `run_gui.py`), 도트 이미지, 캐릭터 데이터. **이 컴퓨터의 사용자**
  - 이 컴퓨터는 중고라 Windows 사용자 폴더 이름이 "염정화"로 되어 있을 뿐, 실제 사용자는 재은. git 커밋 계정도 `emddl457`
- **기영** (GitHub `kiyoung1228`): 백엔드 (`roc/`). 저장소 주인 (`kiyoung1228/EvoTail_Project`)
- 규칙 원본은 팀 규칙 문서 `LEVEL3.pdf`. 과제 원문은 `2026 기초프로젝트-레벨3.pdf`

## 작업 방식 (꼭 지킬 것)
- master에 직접 커밋하지 않는다. 작업마다 **새 브랜치 → 커밋 → push → PR**.
- **merge 규칙 (팀 확정)**: `roc/`를 건드리지 않은 GUI PR은 재은이 직접 merge하고 단톡에 알린다. `roc/`를 건드리거나 게임 규칙이 바뀌는 PR은 기영 확인 후 merge
- 시작 전에 `git pull`로 최신 master를 받는다.
- 새 브랜치는 upstream을 걸지 않고 만든다: `git fetch` 후 `git switch -c 이름 --no-track origin/master`. upstream이 `origin/master`로 걸리면 GitHub Desktop에 Publish가 안 뜸 (이미 걸렸으면 `git branch --unset-upstream 이름`)
- PR 전에 테스트를 돌린다: `python -m unittest discover -s tests` 와 `python test_integrated_flow.py`
- 커밋 메시지에 `Co-Authored-By` 줄이나 Claude 관련 표시를 넣지 않는다. PR 설명에도 "Generated with Claude Code" 같은 줄을 넣지 않는다
- 백엔드(`roc/`)를 고쳐야 하면 최소한으로 고치고, PR 설명에 무엇을 왜 고쳤는지 적는다 (기영 담당 코드).
- ID(`dealer_normal_01` 등)는 세이브 키라서 절대 바꾸지 않는다.
- **status 필드는 master에 들어옴** (기영님 PR #6): `get_snapshot`·`get_animals`의 동물마다 `status` = `{'fullness','mood','fatigue'}` → `'good'/'normal'/'bad'`. `ui-kit`의 임시 커밋(`ea4e87b`)은 master merge 때 버림 (roc/·tests/는 master 그대로)

## 실행
```
pip install -r requirements.txt   # pygame-ce>=2.5 (import pygame 그대로. 예전 pygame은 먼저 uninstall)
python run_gui.py                 # 게임 실행. F5 = 빠르게(5배), F12 = 시연 모드(60배)
python main.py                    # 화면 없이 백엔드만 점검
```
세이브: `saves/game.db` (깃에 안 올라감)

## 코드 구조
```
roc/                 백엔드 (게임 규칙 전부). 표준 라이브러리만 사용
  service.py         GameService: 모든 규칙과 상태. RLock + SQLite 저장
  bridge.py          GameBridge.call('명령', ...) → {'ok','data','error'}. GUI는 이것만 쓴다
  worker.py          GameWorker: 1초마다 게임 시간을 흘리는 백그라운드 스레드 (멀티스레딩 요구사항)
  battle.py          턴제 전투 계산, 적 AI 5종
  autonomy.py        자율행동 (먹이 찾기 / 휴식 / 혼자 놀기 / 자유 행동)
  config.py          가격·보상·시간 등 숫자 상수
data/characters.json 캐릭터 30종 (이름, 단계별 이름·이미지, 능력치)
data/role_caps.json  역할별 단계 MAX
assets/              1단계 이미지 30장, assets/sprites/<ID>_s<단계>.png 75장
  map/               섬 마을 지도 낮·밤 + 클릭 영역 map.json
  ui/                메뉴 아이콘. ui/kit/ = 도트 UI 키트 조각·아이콘 (docs/UI_KIT.md)
  fonts/             갈무리 글꼴 (OFL)
docs/mockups/        확정된 화면 목업 (메인 낮·밤, 설정 창, 내 동물 animals_v2, battle/ 전투장, home/ 주방, shop/ 상점·부화, hospital/ 병원, farm/ 밭)
docs/UI_KIT.md       도트 UI 키트 규칙 (모든 화면이 따름). 조각 다시 만들기: tools/uikit.py
gui/                 Pygame 화면 (아래 GUI 규칙)
CHARACTERS.md        캐릭터 목록 · GUI.md 화면 구조 설명
```

## GUI 규칙
- **모든 화면은 `docs/UI_KIT.md`(도트 UI 키트)를 따른다.** 기준 목업: `docs/mockups/animals_v2.png`, `main_day.png`, `main_night.png`
- 게임 규칙을 GUI에 다시 구현하지 않는다. **읽기 `app.call('명령')`, 바꾸기 `app.act('명령', 성공문구, ...)`**
  - `act`는 실패하면 백엔드가 준 이유를 알림으로 띄우고, 성공하면 상태를 다시 읽는다.
  - 명령 목록: `roc/bridge.py`의 `ALLOWED_COMMANDS`
- 이름·이미지는 백엔드가 **현재 진화 단계 기준**으로 준다 (`name`, `sprite`). 전투 화면의 적도 `name`, `sprite`가 있다.
- 화면 갱신: 메인 루프가 `worker.poll()`로 알림을 확인하고 `app.refresh()`로 `get_snapshot`을 다시 읽는다. 스레드에서 화면을 직접 건드리지 않는다.
- 새 화면: `gui/scenes/`에 `Scene` 상속 (`enter`, `handle`, `update`, `draw`) → `run_gui.py`에서 `PlaceholderScene` 대신 등록.
- 화면 위에 뜨는 창(설정·확인·도움말 등)은 `app.Overlay` 상속 → `app.open_overlay(창)`. 열려 있으면 입력은 맨 위 창만 받고, 뒤는 어둡게. ESC·창 밖 클릭으로 닫힘 (`close_outside`). 확인 창은 `settings.ConfirmOverlay` 재사용
- 시작할 때 `gui/display.py`가 Windows DPI 인식을 켜고(배율 125% 등에서 Windows가 창을 늘려 글씨가 뭉개지는 것 방지), 창은 640×360의 정수배 중 작업 영역에 들어가는 가장 큰 크기(1~3배, `T.SCALE`). 창 확대는 `pygame.transform.scale`(정수배)만
- 화면은 **640×360 논리 화면**에 그리고 App이 창(보통 1280×720)에 정수배로 붙인다. 장면 좌표·마우스 좌표는 전부 논리 픽셀 (상단 바 26 = 창 52px). 마우스 위치는 `widgets.mouse_pos()`
- 색·글꼴·한글 라벨은 `gui/theme.py`, 키트 위젯(`panel`, `card`, `ribbon`, `chip`, `gauge`, `Button(색, icon, sub)`, `icon`)은 `gui/widgets.py`. 둥근 사각형·직접 고른 색으로 새로 그리지 말고 키트 조각을 쓴다
- 지도가 아닌 화면의 배경은 `app.backdrop(surface)`(어둡게 깐 지도), 왼쪽 위 `◀ 지도` 갈색 버튼 + 빨간 리본 제목
- 도트 이미지는 정수배로만 (`SpriteCache.get(path, size)`, size = 28의 배수: 28 원본, 56 = 2배, 84 = 3배). smoothscale 금지
- **적 몬스터** (`assets/enemies`, `data/enemies.json`): 졸개 12종 원본 28×28, 보스 9종(스테이지마다 1) 원본 46×46, 파일은 4배. 화면에서는 둘 다 원본 ×2 (`SpriteCache.scaled(path, 2)` → 졸개 56, 보스 92). 보스 여부는 백엔드 `boss` 값, 없으면 그림 크기(`SpriteCache.is_boss`). 칸이 정해진 곳은 `SpriteCache.fit(path, w, h)` (들어가는 정수배, 안 들어가는 보스는 위쪽을 잘라 초상). 표시 정보(스테이지별 보스)는 `gui/enemies.py`
  - 백엔드 적 name/sprite/boss는 enemies.json 기준 (PR #12, 기영). 스테이지마다 보스 1 + 졸개 2
- 글꼴: 갈무리(`assets/fonts/`, OFL, `Galmuri_LICENSE.txt` 같이 배포). `T.font('title'|'body'|'small'|'big')`로만 쓴다 (크기 12/12/10/15 고정 = 획이 픽셀에 딱 맞는 크기, `tests/test_fonts.py`, 안티에일리어싱 끔)
- **칸 안 글씨**(버튼·간판·메뉴·칩·리본·알림·툴팁 등)는 `widgets.text_in(surface, 글씨, 칸, ...)`: 실제 글자 모양(줄 높이 아님) 기준 정렬. 칸 크기는 글씨에 맞춰 넓힌다(`fit_width`, `Button.width_for`, `BUTTON_H` 20, `CHIP_H` 16, `CARD_LABEL_H` 20). **글자 크기를 줄여서 맞추지 않는다**
- 화면을 바꾸면 `python tools/check_text_fit.py`로 모든 칸 글씨가 사방 2px 여백 안에 있는지 확인 (`shots`를 붙이면 실제 창 크기 스크린샷)
- 알림은 `app.toast(문구, 'ok'|'bad'|'info', 아이콘)`, `app.act(..., icon='home')`처럼 아이콘을 줄 수 있다. **한 번에 1개**(새 알림이 바꿔 낌), 3.5초 뒤 사라짐, **화면을 바꾸면 지움**(`App.go`). 자리는 화면의 `toast_anchor()`: 기본 오른쪽 위(◀ 버튼·제목 리본 피함), 지도 왼쪽 아래, 전투 명령창 바로 위, 결과 왼쪽 위
- 이름 뒤 조사는 `T.josa(이름, '을'|'이'|'은'|'으로'|'과')`로 받침에 맞게. `을(를)`처럼 쓰지 않는다
- 상태 단계(좋음·보통·나쁨)는 백엔드가 동물 행마다 주는 `status`(`{'fullness','mood','fatigue'}` → `'good'/'normal'/'bad'`)를 `T.level(a, kind)`, `T.any_bad(a)`로 읽는다. GUI에서 기준값으로 다시 계산하지 않는다
- 남은 시간·진행 게이지는 `app.now()`(스냅샷 시각 + 그 뒤 흐른 시간 × 배속)로 계산
- 설명 말풍선은 `widgets.tooltip`, 선택 강조는 `widgets.select_frame(색)` (키트 스타일). 말풍선은 화면 가장자리에서 4px 안쪽(`TIP_INSET`), `avoid`(예: 다른 동물 체력바)와 겹치면 반대쪽
- 화면을 만들면 직접 실행해서 확인한다.

## 도트 스타일
- 캐릭터: 원본 28×28 → 4배 확대 112×112, 배경 투명, 진한 테두리, 밝은 파스텔.
- 진화: 동물은 그대로, 속성 효과만 커진다. 불: 불씨→불꽃→화염 / 물: 물방울→개울→파도 / 바람: 산들→구름→하늘. 2단계부터 몸에 속성 무늬, 3단계는 테두리 색이 바뀌고 반짝이.
- 기존 게임(포켓몬, 동물농장 등)의 캐릭터·그림을 따라 그리지 않는다. 분위기만 참고하고 전부 오리지널로.

## 게임 규칙 요약
**역할 = 속성**: 딜러=불, 탱커=물, 힐러=바람. 유형도 딜러형/탱커형/힐러형.
**캐릭터 30종**: 일반 15(2단계까지) + 특급 15(3단계까지), 역할별 5종씩. 같은 역할·등급은 기준값 ±10%.
시작 능력치 기준(체/공/방/민): 일반 딜러 60/90/50/80, 탱커 100/50/90/40, 힐러 60/60/60/60, 특급은 ×1.4.
최초 지급: 불씨여우, 물방울수달, 산들오리 (각 역할 첫 일반 캐릭터).

**역할별 MAX** (단계 기준 300/500/1000 × 배율)
| 역할 | 체력 | 공격 | 방어 | 민첩 |
| --- | --- | --- | --- | --- |
| 딜러 | ×0.8 | ×1.4 | ×0.6 | ×1.2 |
| 탱커 | ×1.4 | ×0.6 | ×1.4 | ×0.6 |
| 힐러 | ×0.9 | ×0.8 | ×0.9 | ×1.0 |

**진화**: 네 능력치 모두 MAX + 코인 (2단계 800, 3단계 3000).
**훈련**: 능력치 하나 선택. 쉬움 10분 +10 / 중간 30분 +30 / 어려움 60분 +65. 포만감·기분 감소, 피로도 증가. 피로도 50 이상이면 효과 절반. 태풍 중 2배.
**상태 3단계** (0~100): 포만감·기분 0~29 나쁨, 30~55 보통, 56~ 좋음. 피로도는 반대 (56 이상 나쁨).
**피로도**: 전투 승리 +30, 패배 +100. 쉬면 5초마다 1 감소, 밤엔 2배. 상태가 나쁨이면 훈련·전투 불가.
**강제 휴식** (PR #6): 피로도 **80 초과**(80은 아님)면 성격과 관계없이 자율행동이 `rest`로 바뀜 (`roc/autonomy.py` `FORCED_REST_FATIGUE_THRESHOLD`). GUI는 `action == 'rest'`만 보고 엎드린 모습으로 표시
**질병**: 훈련·사냥·전투 후 30% 확률. 질병이면 출전 불가. 병원 회복 포션으로 치료 (기본 50%, 고급 90%).
**성격 5종**: 먹보, 잠꾸러기, 장난꾸러기, 평범한, 까칠. 자율행동 경향과 출전 조건에만 영향 (훈련 보너스 없음).
**전투**: 3대3 팀 턴제, 플레이어 선공, 한 턴에 서로 다른 2마리 행동.
- 딜러: 적 전체 공격 (치명타 1.5배, 공격력에 비례)
- 탱커: 공격 또는 아군 하나 절대방어
- 힐러: 공격 또는 아군 하나 회복 (1/2/3단계 100/300/500)
- 특수 기술 쿨타임: 한 번 쓰면 다음 자기 팀 턴 1번만 쉼 (팀 확정, 기영 확인)
- 방어 버튼 (받는 피해 50%), 민첩성 = 회피 확률, 상성 불>바람>물>불 (1.1배 / 0.9배)
- **능력치 포션은 전투 전**(+100, 전투 1번), **응급 붕대는 전투 중**(`battle_bandage`, 체력 +80, 팀 행동 1번 사용). 장비는 미리 착용, 전투 중 교체 불가
**스테이지**: 뉴비(40) → 쉬움(150) → 브론즈(250) → 보통(400) → 실버(500) → 어려움(800) → 골드(900) → 극악(1100) → 다이아몬드(1200). 브론즈~다이아는 대회(첫 클리어 보상).
**사냥터** (자동 사냥): 닭장·돼지우리·목장 30분 고기 3개, 달토끼 언덕 60분 고기 3개.
**요리** (확정, PR #3·#4): 별 1~5 레시피. 타이밍 미니게임 판정을 GUI가 재서 `cook(recipe, judgment)`로 넘긴다. `judgment`는 `'perfect'` / `'good'` / `'miss'` (소문자. 예전 `grade=`/`'Perfect'`도 받지만 GUI는 judgment를 쓴다)
- 결과: `outcome`(`'great'` 대성공 / `'success'` 성공 / `'rescued'` Miss 구제 / `'burnt'` 탄 요리), `xp` = **이번에 받은 경험치**, `total_xp` = 누적 경험치, `level`, `item`(받은 요리 아이템), `effects`
- perfect: 대성공 요리 (먹이 효과 1.5배) / good: 보통 요리 / miss: 탄 요리. 단 ★1~3의 Miss는 숙련도 레벨에 따라 확률로 구제(보통 요리), **구제되면 경험치 없음**. ★4~5 Miss는 항상 탄 요리
- 경험치: 성공(perfect·good) 시 별 × 10. 레벨업 기준 100/300/600/1000
- 미니게임 숫자는 GUI에 적지 말고 백엔드에서 읽는다: `get_rules()['cooking']['timing']`(커서 범위 0~100, 목표 중심 범위, Perfect·Good 반폭, 제한 시간), 레시피별 커서 이동 시간은 `get_recipes()`의 `travel_seconds`. 구제 확률 `miss_rescue_chance`도 `get_recipes()`에 있다
**시간**: 낮 30분 / 밤 30분 반복. 태풍은 1시간마다 10분. 30분마다 15% 확률 보너스 코인 이벤트.

## 아직 팀에서 정하지 않은 것 (임의로 바꾸지 말고 물어볼 것)
- 지금은 없음. 새로 생기면 여기에 적고 물어볼 것

## 팀 확정 (예전에 미정이던 것)
- 가격·보상: **지금 코드 값**(`roc/config.py`)으로
- 달토끼 언덕 고기: **3개** (코드와 같음)
- 출전 조건(상태 나쁨·질병·성격), 훈련 조건, 전투 전 포션(능력치 +100, 그 전투 1번), 대회 단계(브론즈~다이아), 상성 피해(1.1배 / 0.9배): **코드대로**
- 전투 응급 붕대(`battle_bandage`): **유지** (과제 요구사항 "전투 중 아이템 사용"). 전투 화면 "아이템" 버튼으로 씀
- 특수기 쿨타임: 쓰면 **다음 자기 팀 턴 1번 쉼** (기영 확인)

## 메인 화면 (팀 확정: "떠 있는 섬 마을")
목업: `docs/mockups/main_day.png`, `main_night.png`, `settings.png`. 이 모습대로 만든다.

**지도 파일**
- `assets/map/map_day.png`, `assets/map/map_night.png` (1280×720, 글자 없음). 백엔드 `clock.night`에 따라 배경만 바꾼다.
- `assets/map/map.json`: 건물별 클릭 영역 `places.<키>.rect` [x0,y0,x1,y1], 문 위치 `door`, 마당 영역 `yard`. 낮·밤 공통.

**건물 6개** (JSON 키 → 이동할 화면)
| 키 | 간판 | 화면 |
| --- | --- | --- |
| home | 집 | 요리(주방) + 휴식. 원래 주방 건물을 "집"으로 바꿈 |
| shop | 상점 | 먹이·장난감·장비·알 구매, 판매 |
| hospital | 병원 | 질병 치료, 회복 포션 |
| farm | 밭 | 작물 심기·수확 |
| battle | 전투장 | 스테이지·대회 |
| hunting | 사냥터 | 자동 사냥 |
- 간판(나무 판 + 글자)은 GUI가 건물 아래에 그린다. 마우스를 올리면 노란 테두리 + 설명 말풍선.
- 예전 "집" 건물과 "도감" 건물은 없앰. 동물은 밖(마당)에서 지낸다.

**오른쪽 메뉴 5개** (아이콘 `assets/ui/icon_*.png`)
내 동물(`my_animals`, 지금의 AnimalsScene) · 도감(`pokedex`) · 가방(`bag`, 인벤토리) · 마이룸(`my_room`, 처음엔 "준비 중") · 설정(`settings`)

**설정 창** (`gui/scenes/settings.py`, 지도 메뉴 "설정" → 지도 위 창): 시간 속도(보통 / 빠르게 5배), 시연 모드(60배, 영상용), 저장하기(`save_game`), 불러오기(`load_game`, 확인 창 먼저), 도움말, 게임 종료, 마지막 저장 시각.
- 백엔드는 모든 변경을 바로 SQLite에 저장(자동 저장), 종료할 때도 `App.run`이 `save_game`을 부름. 마지막 저장 시각은 스냅샷 `last_saved`(실제 Unix 시각, 자동 저장 포함, PR #9)를 표시
배경음·효과음은 아직 백엔드·에셋이 없음 → 팀 결정 전까지 목업에만 있음.

**상단 바**: "1일차 · 낮 14:20 · 맑음" 순서(낮은 해, 밤은 달 아이콘) + 빠르게면 "· 5배속", 오른쪽 코인. 날짜·시각은 백엔드 `clock['day']`, `clock['time']`('HH:MM')
- 게임 시계 (PR #6, `_clock_view`): 게임 하루 = 가상 60분(낮 30분 + 밤 30분), 1일차 06:00 시작, 가상 2.5초 = 게임 1분, 다음 06:00에 날짜가 넘어감. `timestamp`·`night`·`storm`·`rate`는 그대로

**시간 속도** (`gui/theme.py`의 `SPEED_FAST`, `SPEED_DEMO`)
- F5: 보통(1배) ↔ 빠르게(5배). 평소 플레이용
- F12: 보통 ↔ 시연 모드(60배). **제출 영상 촬영용.** 켜지면 상단 바에 빨간 "시연 모드" 표시
- 설정 창 버튼도 같은 함수(`App.toggle_speed`)를 쓴다

**마당에 보여줄 동물** (최대 수는 하드코딩하지 말고 스냅샷 `yard_max`를 읽는다. 지금 5, PR #4)
- 백엔드: `get_yard_animals()` → `{'keys', 'max'}`, `set_yard_animals(keys)`(**list만** 받음, 보유 동물 0~`yard_max`마리, 중복 불가, 순서 = 표시 순서, 세이브에 저장). 새 게임은 빈 목록으로 시작 → 화면 자동 채우기. 스냅샷에도 `yard`(ID 목록)와 `yard_max`가 있다
- `yard`는 화면 표시용일 뿐 훈련·전투·자율행동에는 영향 없음
1. 플레이어가 "마당에 내보내기"로 고른 동물 = 스냅샷 `yard` (내 동물 화면 버튼 → `set_yard_animals`)
2. `yard`가 `yard_max`보다 적으면 남는 자리는 **화면에서만** 자동으로 채움 (세이브에 안 씀): 마지막 전투 팀 3마리(스냅샷 `last_team`, PR #9) → 돌봐야 하는 동물(배고픔·기분 나쁨, 질병) → 최근에 얻은 동물
3. 나머지는 마당 입구에 "+N마리" 표지판 → 누르면 내 동물 화면
- 활동 중인 동물은 마당 대신 그 장소 앞에 작게: 사냥 중 → 사냥터, 훈련 중 → 집, 아픔 → 병원
- 마당에 안 보여도 백엔드는 모든 동물의 자율행동·상태를 계속 계산한다 (화면 표시만의 문제)
- 밤에는 말풍선을 "잠자는 중 zZ" 등으로, 동물 도트는 약간 어둡게
- **드러눕기 (팀 결정, 임시)**: 자율행동 `action == 'rest'`이거나 포만감·기분·피로도 중 하나라도 "나쁨"이면 엎드림. 엎드린 동안 안 돌아다니고 몸 윗부분이 1px씩 천천히 숨쉼. 하나라도 "나쁨"이면 회색 찡그린 얼굴(`frown`) 말풍선 + 도트 살짝 어둡게
  - 언제 눕는지는 GUI가 정하지 않고 백엔드 값(`action`, 동물 행의 `status`)만 읽는다
  - 누운 그림은 `SpriteCache.lying()` 하나에서 만든다. 지금은 "엎드리기": 서 있는 도트를 세로만 원본 28줄 → 20줄로 고르게 줄 빼서 납작하게, 바닥에 붙임 (90° 회전은 쓰러진 것처럼 보여서 안 씀). `assets/sprites/<ID>_s<단계>_lying.png`를 그려 넣으면 자동으로 그 그림을 씀

## 전투장 (목업 `docs/mockups/battle/`, 팀 결정 = 스테이지 2화면 + 전투 A안 + A2_1~3)
- **스테이지 고르기** (`gui/scenes/battle_stage.py` `StagePickScene`, stage_pick.png): 9단계를 뱀 모양 길로 잇고 동그라미 안에 보스 얼굴(`gui/enemies.py` → data/enemies.json). 깬 곳 초록 체크, 잠긴 곳 자물쇠(못 고름), 대회는 메달 색 테두리. 오른쪽에 보스 그림·대회·전투력·보상·상대 성향, "팀 정하기"
- **출전 준비** (`TeamPrepScene`, stage_team_prep.png): 상대(`preview_stage`) vs 내 팀(`last_team`으로 미리 채움, ✕로 빼기). 다른 동물은 스냅샷 `participation`/`participation_reason`(백엔드 `_available`, `can_participate`와 같음)으로 출전 불가면 흐리게 + 이유. 전투 전 포션은 카드를 누를 때마다 팀원에게 차례로(한 마리에 하나). 출전 = `start_battle(stage, team, prebattle_potions)`
- **전투** (`gui/scenes/battle_fight.py` `BattleScene`): 아군 왼쪽·적 오른쪽, 머리 위엔 체력바만(이름은 마우스), 보스는 원본 46 ×2. 명령창 = 고른 동물 정보 + 공격/특수기/방어/턴 넘기기, `get_battle_actions`가 준 행동만 켬
  - 딜러의 공격은 백엔드에서 **적 전체 공격**이라 대상 고르기 없음. 딜러는 특수기 버튼이 없음 (탱커 = 절대방어, 힐러 = 회복)
  - 특수기 버튼은 역할 상관없이 **보라색**(방어 파랑과 구분). `cooldown`이 0보다 크면 회색(disabled) + "재사용 대기: 1턴", 발밑 칩 "기술 쉼". 버튼 아래 설명 "아군 1마리 / 쓰면 다음 턴 1번 쉼"
  - 작은 기록 칸은 "주체 → 대상 숫자" 한 줄 ("야생" 빼고, 길면 이름만 줄임), 펼친 기록은 전체 문장
  - 대상 고르기: 위 안내 띠 + 꺾쇠(적 빨강·아군 초록·마우스 올린 대상 노랑), ESC·오른쪽 클릭 취소. 회복은 체력바에 회복 뒤 체력 미리보기
  - 백엔드는 한 번 호출에 내 행동 + 적 차례까지 처리 → 응답의 전투 기록(events)을 재생: 내 행동은 바로, 적 차례는 0.6초 간격. 체력바·숫자는 기록 값(피해·회복)으로만 움직이고 끝나면 백엔드 체력으로 맞춤
  - 전투 기록: 작은 칸, 마우스를 올리면 위로 펼침(라운드·"적" 칩). 도망가기 = `forfeit_battle`(확인 창)
  - 회복 미리보기 = `get_battle_actions`의 행동마다 `amount`(PR #12, 그 대상에게 실제로 회복될 양). `HEAL_PREVIEW` 표는 amount가 없을 때만 + 회복 버튼 글씨(최대 회복량)
  - 한 마리가 행동하면 **아직 행동 안 한 아군을 자동으로 고른다** (없으면 고른 동물 그대로)
  - **전투 아이템**: 명령창 "아이템 N" 버튼(가방에 전투 아이템이 있을 때만 켜짐) → 버튼 위 목록(이름 ×개수 · 회복량 · 팀 행동 1번 사용) → 고르면 아군 대상 고르기(초록 꺾쇠, 회복 뒤 체력 미리보기). `get_battle_actions(actor='battle_bandage')`의 `battle_item` 행동만 씀 → `battle_action(actor='battle_bandage', kind='battle_item', target)`
    - 백엔드 동작: 붕대는 팀 행동 1번(한 턴 2번 중)을 쓰지만 동물 한 마리의 "행동 완료"로 치지 않음. 회복량 = min(80, 모자란 체력), 기록 이벤트 `battle_item`의 `amount`
    - 미리보기 회복량은 `battle_item` 행동의 `amount` (없을 때만 상점 목록 `heal`)
- **결과** (`BattleResultScene`): 승/패, 보상 코인(`battle_result.reward`), 첫 대회 우승/처음 깸(`first_clear`) + "다음 단계 열림"(get_stages의 다음 order), 팀 피로도 전→후(출전 직전 스냅샷과 지금 스냅샷, 둘 다 백엔드 값), 아픔 표시
- 전투장 배경(관중석·벽·깃발·모래)은 그림 파일이 없어 코드로 그린 도트 (`arena_surface`)

## 집 · 주방 (목업 `docs/mockups/home/`, `gui/scenes/home_kitchen.py` `KitchenScene`)
지도 "집" 건물 → 주방. 배경 `assets/home/kitchen.png`(1280×720 = 논리 640×360의 2배 → ½로 그대로). 왼쪽 위 ◀ 지도 + 빨간 리본(집 · 주방 / 요리 중 / 요리 완성), 오른쪽 위 요리 레벨 칸(누적 경험치 / 다음 레벨 기준, `get_recipes`의 level·xp, `get_rules()['cooking']['level_thresholds']`)
- **레시피 북** (home_1_book): 책(panel) 위 책갈피 탭 "레시피"(빨강) / "음식 주기"(초록). 왼쪽 쪽 = 레시피 칸(그림·이름·별), 재료가 모자라면 회색. 오른쪽 쪽 = 큰 그림(×4)·이름·별·한 줄 설명·재료(가진 수/필요 수)·먹으면 효과(`get_shop_catalog()[regular_item]['effects']`)·"대성공이면 N배 · 경험치 +N"(`perfect_multiplier`, `xp_per_star`)·요리 시작
  - 재료 부족 (home_1b_missing): 그림은 색 그대로, "N가지 부족" 빨강, 모자란 재료 칸 빨간 테두리·빨간 숫자 + "구하기: 밭/사냥터/상점", 충분하면 초록 숫자 + "충분함!", 버튼은 회색 "재료가 부족해요"
  - 구하는 곳은 백엔드 값으로: 상점 목록 kind `crop` = 밭, `get_hunts` 사냥터 보상 item = 사냥터, `buy`가 있으면 상점
  - 한 줄 설명만 GUI 표시 문구 (`gui/food.py` `DESCRIPTION`, 백엔드에 설명 없음)
- **미니게임** (home_2_bar): 난로 위 프라이팬 + 재료 그림, 위에 이름·별, 오른쪽 위 남은 시간. 아래 막대: 커서가 끝→끝 `travel_seconds`(레시피) 동안 왕복, 목표 중심은 `target_center_min~max` 무작위, 중심 ± `good_half_width` = Good(주황), ± `perfect_half_width` = Perfect(노랑). Space(또는 막대 클릭) 한 번에 판정 → `cook(recipe, judgment)`. `timeout_seconds` 안에 안 누르면 miss. ESC는 그만두기(cook 전이라 재료 그대로). 숫자는 전부 `get_rules()['cooking']['timing']`
- **결과** (home_3_result): outcome별 `great` 대성공(초록 리본·빛줄기·PERFECT·효과 1.5배) / `success` 성공 / `rescued` "아슬아슬 성공! (경험치 없음)"(갈색) / `burnt` 탄 요리(빨강, MISS). 요리 그림·이름·효과(결과 `effects`), 레벨 게이지(이번에 오른 부분은 밝게, `xp`·`total_xp`), 레벨 업 칩. 버튼 "한 번 더"(재료 없으면 꺼짐) / "동물에게 주기"(음식 주기 탭에 방금 요리를 골라 둠)
- **음식 주기** (home_4_feed): 왼쪽 = 가진 요리(`food_*`, `food_perfect_*`, `burned_food`) + 개수, 대성공은 별 배지. 오른쪽 = 고른 요리 효과 + 동물 목록(포만감 게이지, 고른 동물은 먹은 뒤 포만감을 연두색으로 미리보기 "42→87", 포만감 나쁨이면 "배고파요" 칩, 활동 중(훈련·사냥·전투)이면 흐리게 + 이유, 4줄 넘으면 휠). "○○에게 주기" = `use_item(item, key)`. 탄 요리는 "반쯤은 안 먹어요", `refused`면 알림

**음식 그림** (`assets/food/`, `gui/food.py`)
- 원본 16×16, 파일은 4배(64). `FoodIcons.get(item, n)`으로 원본 × n (화면에서는 ×1~×4 정수배만)
- 파일 이름 = 백엔드 id (재료 `potato.png`, 레시피 `butter_potato.png`). `food_<id>`, `food_perfect_<id>`는 레시피 그림을 쓰고 대성공은 그림을 가리지 않는 작은 별 배지(`star_badge`). 대성공 요리 이름은 "대성공 감자버터구이"
- 이름: 재료는 백엔드 상점 목록 label (없으면 `assets/food/food_icons.json` name). 그림이 없는 재료(돼지고기·양배추)는 키트 아이콘으로 대신
- 다시 만들기: `tools/food_icons.py`(음식 그림), `tools/home_mock.py`(주방 목업·배경)
  - **감자·양파·밀 재료 아이콘**(`potato.png`·`onion.png`·`wheat.png`, 밭 그림과 같은 모양)은 `tools/crops_v8.py`의 `potato_icon()`·`onion_icon()`·`wheat_icon()`, 쌀은 `tools/farm_icons.py`의 `rice_icon()`으로 만든다 (`tools/food_icons.py`의 같은 이름 그림은 옛 그림)
  - **쌀 재료 그림**(`assets/food/rice.png`, 삼베 자루 + 흰 쌀)은 `tools/farm_icons.py`의 `rice_icon()`으로 만든다. `tools/food_icons.py`의 `rice()`는 옛 그림이라 쓰지 않음. 다 자란 벼(`rice_ripe.png`, 고개 숙인 벼)도 `farm_icons.py`의 `ripe_rice()` v4

## 상점 · 알 부화 (목업 `docs/mockups/shop/`, `gui/scenes/shop.py` `ShopScene`, `gui/scenes/hatch.py`)
지도 "상점" 건물 → 상점. 배경 `assets/shop/shop.png`(1280×720, ½로 그대로, 위 26px 투명 = 상단 바 자리)
- **탭 6개** (`gui/items.py` `TABS`, 상점 목록 `kind`로 나눔): 먹이·장난감(snack·toy) / 회복·포션(cure·prebattle·battle_item) / 장비(equip) / 알(egg) / 재료·씨앗(ingredient·seed) / 팔기(빨간 글씨, 가방에 있고 `sell`이 있는 것). 사는 탭은 `buy`가 있는 것만
- 가운데 3열 칸: 그림 ×2, 이름(길면 두 줄 `widgets.wrap2`, 줄이지 않음), 코인 가격, 가진 개수는 그림 오른쪽 아래 회색 칩 "×N". 3줄 넘으면 휠
- 오른쪽 상세: 그림 ×3, 이름(big), 종류 칩, 효과 줄(`items.effect_lines`, 숫자는 전부 `get_shop_catalog`), "보유 N", 수량 - N +(최대 99, 팔기는 가진 수까지), 합계, "구매"(아래 "N개 · N코인") = `buy_item(item, quantity)` / 팔기 탭은 "판매" = `sell_item`. 실패 이유(코인 부족, 쓴 장난감 등)는 백엔드 알림
- 장비 상세: "내 동물 화면에서 장착", "전투 중 교체 불가". 내 동물 화면 아래 파란 "장비" 버튼 → `EquipOverlay`(가방 장비 장착 `equip(key, item)` / 해제 `equip(key, None)`)
- **알 탭**: 진한 배경 + 빛줄기 위 알, "특급 등장 확률" 금색 막대. 확률(특수 60% / 기본 10%)은 백엔드 `hatch_egg` 안의 숫자라 API로 안 나옴 → **GUI 표시 문구** `items.EGG_SPECIAL_RATE`. 백엔드 확률을 바꾸면 여기도 바꿀 것 (기영님께 `get_rules`로 내 달라고 요청 가능). 보유하면 초록 "지금 부화"
- 문구는 게임 말투 ("~요" 대신 "보유 2", "출전 불가", "~샀다")
- **부화 연출** (`HatchOverlay`, hatch_1_storyboard): 총 2.6초, 클릭·Space·ESC로 건너뛰기. ① 0~1.2초 흔들흔들(±4px, 점점 빠르게) + 은은한 빛 ② 1.2~2.2초 금 1줄 → 여러 줄, 금에서 빛, 빛줄기 회전 ③ 2.2~2.6초 하얀 빛 폭발 + 껍질 위/아래 조각 + 반짝이 ④ 결과 창. `hatch_egg(egg)`는 연출 시작할 때 한 번(실패하면 연출 없이 알림). 알 그림 ×5
- **부화 결과** (hatch_2_result / hatch_3_duplicate): 왼쪽 빛줄기 무대 + 동물 원본 ×4 + 껍질 조각, 새 동물이면 빨간 "NEW". 오른쪽 이름, 칩(특급 금색 / 일반 회색, 역할, 속성, "강점 ○○" = 캐릭터 `strength`, '기준'은 "균형"), 설명(`get_catalog` description), "도감 등록! N / 30"(`hatch_egg`의 owned / 캐릭터 수) 또는 중복이면 빨강 "이미 보유한 동물 · 도감 변화 없음", 능력치 4줄(`get_evolution_status`의 stats·caps), 버튼 내 동물 보기 / 한 번 더 부화(같은 알 개수, 없으면 회색) / 상점으로

## 병원 (목업 `docs/mockups/hospital/`, `gui/scenes/hospital.py` `HospitalScene`)
지도 "병원" 건물 → 병원. 그리는 순서: `assets/hospital/room.png` → 환자(원본 ×3, 논리 (236, 92), `assets/items/items_icons.json`의 hospital) → `blanket.png`(이불이 가슴까지)
- 위: ◀ 지도 + 리본 "병원" + 아픈 동물 탭(얼굴 16px + 이름, 스냅샷 `sick`). 없으면 빈 침대 + "아픈 동물 없음"
- 가운데: 침대 환자 + 땀방울 + "아픔" 말풍선. 오른쪽 정보 칸: 이름, 칩(아픔 / 출전 불가), 피로도·포만감 게이지 + `T.level` 단계, "훈련·사냥·전투 불가"
- 아래 쟁반: "치료할 포션 선택", 기본/고급 회복 포션 카드("치료 50% · 피로도 -10" = 상점 목록 chance·fatigue, 보유 N, 0이면 빨강), "치료하기"(아래 "○○ 1개 사용"), "포션 사러 가기 ▶ 상점"(상점 회복·포션 탭)
- 치료 = `use_item(item, key)` → `CureResult`(Overlay): success면 빛줄기·"○○ 회복!"·피로도 전→후(전 = 호출 직전 스냅샷, 후 = 응답 fatigue)·다음 환자/닫기, 아니면 회색·"○○ 아직 아픔"·"포션 1개 소모"·다시 치료/닫기

**아이템 그림** (`assets/items/`, `gui/items.py` `ItemIcons`): 원본 16×16, 파일 4배(64). 화면에선 ×1~×3 정수배만. 씨앗은 작물별 봉투 `seed_<작물>.png`, 없을 때만 `seed.png`. 그림이 없으면 `assets/food` 그림, 그것도 없으면 키트 아이콘. 다시 만들기: `tools/shop_icons.py`, 목업 `tools/shop_mock.py`·`shop_mock2.py`, 병원 배경 `tools/hosp_room.py`

## 밭 (목업 `docs/mockups/farm/`, `gui/scenes/farm.py` `FarmScene`, A안)
지도 "밭" 건물 → 밭. 배경 `assets/farm/farm.png`(1280×720, ½로 그대로, 위 26px 투명)
- 위: ◀ 지도 + 리본 "밭" + 정보 칸 "심고 10분 · 수확 3개". 다 자란 밭이 하나라도 있으면 그 자리에 주황 "모두 수확" → ready인 밭마다 `harvest_crop(index)`을 차례로, 끝나면 짧은 알림 한 번 "6칸 수확 · 작물 18개"(칸 수·개수는 실제 수확 결과). 한 칸 수확은 "토마토 +3"
- 왼쪽 텃밭 6칸(3열 × 2줄, 나무 틀 + 흙 점무늬는 코드로 그림 `soil_tile`, tools/farm_mock.py soil()과 같음). 상태는 스냅샷 `plots`(index, crop, ready, end, remaining_seconds), 남은 시간은 `end - app.now()`로 계속 줄어듦
  - 자라는 중: 왼쪽 위 갈색 칩 "4:12" + 아래 초록 진행 게이지 / 다 자람: 초록 칩 "수확!" + 천천히 깜빡이는 반짝이 / 빈 밭: "빈 밭" + 고른 칸에 고른 씨앗 새싹 반투명 미리보기(씨앗이 있을 때)
  - 안 산 칸: 풀밭 + 팻말. 바로 다음 칸만 밝은 팻말 "밭 넓히기 + 코인"(`get_rules()['plot_costs'][칸 번호]`, 최대 칸 수 = plot_costs 길이), 그 뒤는 어두운 팻말 "잠김". 고른 칸은 노란 꺾쇠(`select_frame`)
- 오른쪽 칸: 빈 밭 = 씨앗 카드 2열 × 3줄(봉투 ×2, 이름, "보유 N", 0이면 빨강 + 반투명), "씨앗 1개 → 감자 3개", "씨앗은 상점에서 N코인"(상점 목록 buy), "감자 심기"(아래 "10분 뒤 수확", 씨앗 0이면 회색 "씨앗 없음") = `plant_crop(index, crop)` / 자라는 중 = 큰 그림 ×3, 남은 시간 + 게이지, "다 자라면 감자 ×3" / 다 자람 = "수확 가능" 칩, 큰 그림, "받는 것: 토마토 ×3", "가방 보유 2 → 5", "수확하기" = `harvest_crop(index)` / 안 산 칸 = 팻말 + 가격 + "밭 넓히기" → 확인 창 → `expand_plot`(코인 부족 등은 백엔드 알림)
- 수확하면 그 칸에서 작물 아이콘 3개가 위로 톡 튀었다 사라짐(0.6초, 그동안 "빈 밭" 글씨·새싹 미리보기 숨김) + "토마토 +3" 알림
- **작물 그림** `assets/farm/plants/`: seeded / sprout / growing / `<작물>_ripe` (원본 24×24, 파일 4배 96). 밭 칸 ×2(48), 오른쪽 ×3(72). 단계는 진행 = 1 - 남은 시간 / 자라는 시간 → `plants.json`의 구간(0~20% seeded, 20~55% sprout, 55~100% growing, ready면 ripe)
  - **한 칸 = 한 포기 그림(×2) 6번**: 위치는 `plants.json`의 `plot_fill.positions`(칸 132×108 기준, 칸 왼쪽 위에서 48px 그림의 왼쪽 위, 순서대로 = 뒷줄 먼저), `flip_odd`면 홀수 번째(1·3·5)는 좌우 뒤집기, 칸이 132보다 넓으면 가운데 맞춤. 위치 숫자는 코드에 적지 않고 json에서 읽음 (`FarmScene._fill`). 빈 밭 새싹 미리보기도 6포기. 칩·게이지·반짝이는 작물 위에. 오른쪽 상세 칸은 한 포기 ×3
  - 수확 연출이 시작되면 그 칸의 6포기는 바로 사라짐 (백엔드에서 빈 밭이 됨)
  - 다시 만들기: 감자·양파·밀 다 자란 그림은 `tools/crops_v8.py`, 나머지(토마토·쌀·양배추 다 자람, 성장 단계, 씨앗 봉투)는 `tools/farm_icons.py`
- **GUI 표시값** (`farm.FARM_DISPLAY`): 자라는 시간 600초, 수확 개수 3개. 백엔드 `config.CROP_DURATION`·`CROP_YIELD`인데 `get_rules`·스냅샷에 안 나와서 GUI에 둠. 백엔드 값을 바꾸면 같이 바꿀 것 (기영님께 `get_rules`에 넣어 달라고 요청 가능). 밭 가격은 `get_rules()['plot_costs']` 백엔드 값
- 작물·씨앗 이름은 상점 목록 label. 양배추 재료 그림 `assets/food/cabbage.png`(food_icons.json에 추가)
- 다시 만들기: `tools/farm_icons.py`(작물·성장 단계·씨앗 봉투), `tools/crops_v8.py`(감자·양파·밀 다 자람), `tools/farm_mock.py`(목업·배경)

## 진행 상황
- 완료: 백엔드 1차(기영), 캐릭터 30종 데이터, 역할별 MAX, 도트 75장 (PR #1 merge됨)
- 완료 (PR #2 merge됨): 진화 단계별 이름·이미지를 백엔드가 반환, GUI 뼈대, 텍스트 카드 지도(임시), 집 화면(상태·능력치·간식·훈련·진화), 시간 속도 F5/F12
- 완료: 섬 마을 지도 낮·밤, 메뉴 아이콘, 화면 목업 (`assets/map`, `assets/ui`, `docs/mockups`)
- 완료 (PR #3 merge됨, 기영): 마당 저장(`yard`), 요리 타이밍 판정(`cook(recipe, grade)`), 요리 숙련도 확정안
- 완료 (PR #5 merge됨): 메인 화면 섬 마을 지도, 마당 백엔드 연결, 내 동물 화면 "마당에 내보내기/들여보내기"
- 완료 (PR #6 merge됨, 기영): 강제 휴식(피로도 80 초과), 게임 시계 day/time, 동물 status
- 완료 (PR #9 merge됨, 기영): 스냅샷 `last_team`(마지막 출전 팀 ID 3개, `start_battle` 때 저장), `last_saved`(실제 시각, 자동 저장 포함)
- 완료 (merge됨): 도트 UI 키트(640×360 논리 화면, 갈무리 글꼴), 내 동물 화면 animals_v2, 지도 메뉴·간판·알림, 설정 창, 전투장(PR #10, 스테이지 고르기·출전 준비·전투·결과), 전투 아이템(PR #11)
- 완료 (PR #12 merge됨, 기영): 적 몬스터 enemies.json 연결, 전투 행동 회복량 `amount`, 스테이지 `ai_description`
- 완료 (PR #13 merge됨): 집·주방 (레시피 북·재료 부족·요리 미니게임·결과·음식 주기), 전투 다음 동물 자동 선택
- 완료 (PR #14 merge됨): 상점(탭 6개·구매·판매)·알 부화 연출·병원·내 동물 장비 장착, 키트 금색(gold)
- 진행 중 (브랜치 `farm`): 밭(텃밭 6칸·씨앗 심기·수확·모두 수확·밭 넓히기), 작물별 씨앗 봉투, 양배추 그림

## 다음 할 일 (순서대로)
1. **메인 화면을 목업대로**: `map_scene.py`의 텍스트 카드를 지도 이미지 + 간판 + 오른쪽 메뉴로 교체. 마당 동물은 `map.json`의 `yard` 안에서 움직이게. 지금의 "집" 화면(AnimalsScene)은 메뉴 "내 동물"로 연결
2. **설정 창** (시간 속도, 시연 모드, 저장·불러오기, 게임 종료)
3. **전투장**: 스테이지 선택(적 미리보기 `preview_stage`), 팀 3마리 + 전투 전 포션 선택, 전투 화면(체력바, 행동 버튼은 `get_battle_actions`로), 결과 화면
4. ~~상점(구매·판매·알 부화)~~, ~~병원(치료)~~ (완료, PR #14), ~~밭~~ (완료, 브랜치 `farm`), 사냥터, 도감(없는 동물은 실루엣), 가방. (집 주방 + 타이밍 미니게임 = 완료, PR #13)
5. 마이룸(여유 있으면)
6. 실행 파일(PyInstaller), 보고서, **시연 영상(F12 시연 모드)**
