"""아직 만들지 않은 화면. 다음 단계에서 하나씩 실제 화면으로 바꾼다. (키트: docs/UI_KIT.md)"""
from .. import theme as T
from ..app import Scene
from ..widgets import text, text_width, panel, ribbon, Button, BUTTON_H


class PlaceholderScene(Scene):
    def __init__(self, app, title):
        super().__init__(app)
        self.title = title
        self.back = Button((12, 32, max(56, Button.width_for('지도', icon=True)), BUTTON_H), '지도', lambda: app.go('map'),
                           'brown', icon='back')

    def handle(self, event):
        self.back.handle(event)

    def draw(self, surface):
        self.app.backdrop(surface)
        self.back.draw(surface)
        ribbon(surface, (78, 33, max(92, text_width(self.title, 'title') + 30), 18), self.title, 'red')
        box = (T.WIDTH // 2 - 130, 140, 260, 80)
        panel(surface, box)
        text(surface, self.title, (T.WIDTH // 2, 168), 'big', T.TEXT, 'center')
        text(surface, '준비 중 · 다음 단계에서 만들 화면', (T.WIDTH // 2, 192), 'body', T.TEXT_SOFT, 'center')
