"""아직 만들지 않은 화면. 다음 단계에서 하나씩 실제 화면으로 바꾼다."""
from .. import theme as T
from ..app import Scene
from ..widgets import text, panel, Button


class PlaceholderScene(Scene):
    def __init__(self, app, title):
        super().__init__(app)
        self.title = title
        self.back = Button((40, 72, 120, 44), '‹ 지도', lambda: app.go('map'), color=T.INK_SOFT)

    def handle(self, event):
        self.back.handle(event)

    def draw(self, surface):
        surface.fill(T.BG)
        self.back.draw(surface)
        box = (T.WIDTH // 2 - 260, 260, 520, 180)
        panel(surface, box)
        text(surface, self.title, (T.WIDTH // 2, 315), 30, T.INK, bold=True, anchor='center')
        text(surface, '다음 단계에서 만들 화면이에요', (T.WIDTH // 2, 370), 18, T.INK_SOFT, anchor='center')
