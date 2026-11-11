# EvoTail 도트 UI 키트

모든 화면은 이 키트로 그린다. 기준 목업: `docs/mockups/animals_v2.png` (내 동물 화면), `main_day.png`, `main_night.png`.

## 핵심 규칙: "1배로 그리고 2배로 키운다"

- 화면은 **640×360 논리 해상도**로 생각하고, 실제 창(1280×720)에는 **2배**로 보인다.
- 가장 쉬운 구현: 640×360 `Surface`에 전부 그린 뒤 매 프레임 `pygame.transform.scale(surface, (1280, 720))`로 창에 붙인다. 마우스 좌표는 `// 2`.
  - 이렇게 하면 글씨·테두리·아이콘이 전부 같은 픽셀 크기라 지도와 어울린다.
- 도트 이미지는 항상 정수배로만 키운다 (`pygame.transform.scale`, 부드럽게 하는 smoothscale 금지).
- 캐릭터 도트: `assets/sprites/*.png`는 112×112(원본 28×28의 4배). 논리 화면에서는 28×28로 줄여서(÷4) 쓰고, 필요하면 2·3배.

## 글꼴 (`assets/fonts/`, 갈무리, OFL 1.1)

| 용도 | 파일 | 논리 크기 |
| --- | --- | --- |
| 제목·버튼·이름 | `Galmuri11-Bold.ttf` | 12 |
| 본문 | `Galmuri11.ttf` | 12 |
| 작은 글씨·칩·게이지 숫자 | `Galmuri9.ttf` | 10 |
| 큰 이름 (상세 화면 동물 이름) | `Galmuri14.ttf` | 15 |

- 위 크기 그대로만 쓴다 (도트 글꼴은 정해진 크기에서만 깨끗함). 2배는 화면 확대로 처리.
- 안티에일리어싱 끄기: `font.render(text, False, color)`.
- 밝은 글씨에는 1px 그림자(오른쪽 아래, 버튼 색의 가장 어두운 색)를 깐다.
- `Galmuri_LICENSE.txt`를 같이 배포한다 (OFL 조건).
- `gui/theme.py`의 `font()`가 지금은 `assets/fonts`의 첫 파일 하나만 쓰므로, 위 표대로 용도별로 고르게 바꿔야 함.

## 9-slice 조각 (`assets/ui/kit/`, 크기와 가장자리는 `ui_kit.json`)

조각의 네 모서리는 그대로, 가장자리는 늘리고, 가운데는 채워서 원하는 크기를 만든다.

| 조각 | 크기 | 가장자리 | 용도 |
| --- | --- | --- | --- |
| `panel.png` | 32×32 | 8 | 큰 창 (양피지 + 나무 테두리) |
| `card.png`, `card_selected.png` | 24×24 | 6 | 목록 칸, 알림, 상단 바의 작은 칸, 선택 강조 |
| `button_<색>_<상태>.png` | 24×16 | 5 | 버튼. 색: green, orange, purple, red, brown, blue, gray / 상태: normal, hover, pressed, disabled |
| `gauge_frame.png` | 16×8 | 3 | 게이지 틀 (채움은 코드로) |
| `ribbon_<색>.png` | 40×16 | 9 | 제목 리본 (red, brown, green). 높이 18로 늘려 씀 |

```python
def nine_slice(img, margin, w, h):
    sw, sh = img.get_size(); m = margin
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    xs = [(0, m, 0, m), (m, sw - m, m, w - m), (sw - m, sw, w - m, w)]
    ys = [(0, m, 0, m), (m, sh - m, m, h - m), (sh - m, sh, h - m, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            if dx1 > dx0 and dy1 > dy0:
                part = img.subsurface((sx0, sy0, sx1 - sx0, sy1 - sy0))
                out.blit(pygame.transform.scale(part, (dx1 - dx0, dy1 - dy0)), (dx0, dy0))
    return out
```
같은 크기를 매 프레임 다시 만들지 않도록 `(이름, w, h)`로 캐시한다.

### 버튼
- 버튼 조각은 아래 2줄이 그림자(입체). 눌렀을 때(pressed)는 그림자가 없어지고 1px 내려간다.
- 글씨: 굵은 갈무리11, 흰색 + 1px 그림자. 아이콘이 있으면 글씨 왼쪽에 12×12 아이콘.
- 두 줄 버튼(훈련 난이도): 위 줄 굵은 글씨, 아래 줄 갈무리9.
- 비활성은 `disabled` 조각 + 글씨 연회색. 마우스를 올리면 `hover`.

### 게이지
1. `gauge_frame` 9-slice로 틀 (높이 8~10)
2. 안쪽(틀에서 2px 안)에 채움: 본색으로 채우고, 맨 윗줄은 밝은색, 맨 아랫줄은 어두운색
3. 10%마다 아래쪽에 1px 눈금
- 색 팔레트는 `ui_kit.json`의 `colors.gauge_fill` (각 색 4단계: 가장 어두움 → 밝음, 본색은 [2])
- 상태: 좋음 green, 보통 orange, 나쁨 red / 능력치: 체력 red, 공격 orange, 방어 blue, 민첩 green

### 칩 (작은 태그)
코드로 그림: 본색 사각형 + 검은 1px 테두리 + 윗줄 밝은색 + 갈무리9 흰 글씨. 역할(딜러 orange, 탱커 blue, 힐러 green), 속성, 등급, 단계, 성격, "마당" 표시에 사용.

## 아이콘 (`assets/ui/kit/icons/`, 12×12)
heart(체력·출전 가능), sword(공격), shield(방어), wing(민첩), meat(포만감), smile(기분), zzz(피로도·잠), coin(코인·가격), sun(낮), snack(간식), home(집·마당), back(뒤로)

## 화면 공통 배치
- **배경**: 각 화면은 지도 그림(`assets/map/map_day.png` / `map_night.png`)을 어둡게(밝기 55%, 채도 70%) 깔고 그 위에 창을 띄운다. 단색 배경 금지.
- **상단 바** (높이 26): 나무 판자(나무색 + 40px마다 세로 이음새), 왼쪽 `EvoTail` 로고, 가운데 시간·날씨 칸, 오른쪽 코인 칸 (작은 칸은 `card` 조각).
- **제목**: 화면 왼쪽 위에 `◀ 지도` 갈색 버튼 + 화면 이름 빨간 리본.
- **알림(토스트)**: 상단 바 바로 아래 가운데, `card` 조각 + 왼쪽 4px 색 막대(성공 green, 실패 red) + 아이콘 + 본문 글씨. 내용을 가리지 않게 창보다 위.

## 키트 다시 만들기
`tools/uikit.py`가 조각을 그리는 코드. 색이나 모양을 바꾸려면 이 파일을 고친 뒤 `export_kit()`로 다시 뽑는다 (Pillow 필요).
