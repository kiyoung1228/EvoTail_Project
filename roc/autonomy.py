"""State-driven, personality-sensitive autonomous behavior for idle animals.

Autonomy intentionally does *not* mint food/coins or silently consume the player's
inventory. Hunger is a request to the player; play has a small capped mood benefit;
rest is reflected in the existing passive fatigue recovery rule.

Decision policy is deterministic given a creature's current state. This makes it
possible to test personalities and to resume after real-world offline time without
relying on a long-lived background process.
"""
from __future__ import annotations

from dataclasses import dataclass

ACTION_LABELS = {
    'eat': '먹이 찾기', 'rest': '휴식', 'play': '혼자 놀기',
    'idle': '자유 행동', 'refuse': '활동 거부',
    'training': '훈련 중', 'hunting': '자동 사냥 중', 'battle': '전투 중',
}

# Thresholds are proposal values; independent of the *confirmed* three-tier status
# labels and nature-specific permission rules in GameService._available.
PREFERENCE_BONUS = 35
ACTION_THRESHOLD = 45
PERSONALITY_FOCUS = {
    'glutton': 'eat',
    'sleepy': 'rest',
    'playful': 'play',
    'balanced': None,
    'picky': 'rest',
}

@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    priorities: dict[str, int]

    def as_dict(self):
        return {'action': self.action, 'label': ACTION_LABELS[self.action],
                'reason': self.reason, 'priorities': dict(self.priorities)}


def evaluate(animal: dict) -> Decision:
    """Return chosen idle action, explanatory reason and behavior priority values.

    A severe shortage beats a modest personality preference. Otherwise a temperament
    bonus makes glutton/sleepy/playful differ from neutral animals in the same state.
    Picky animals can refuse to engage instead of pretending to have fed themselves.
    """
    fullness = max(0, min(100, animal['fullness']))
    fatigue = max(0, min(100, animal['fatigue']))
    mood = max(0, min(100, animal['mood']))
    nature = animal['nature']

    scores = {'eat': 100-fullness, 'rest': fatigue, 'play': 100-mood}
    severe = {'eat': fullness < 30, 'rest': fatigue > 55, 'play': mood < 30}
    if nature == 'picky' and any(severe.values()):
        return Decision('refuse', '까칠한 성격: 상태가 나빠 자율 활동 거부', scores)

    preferred = PERSONALITY_FOCUS.get(nature)
    if preferred is not None:
        scores[preferred] += PREFERENCE_BONUS

    # Real crisis takes priority over a personality preference for a healthy stat.
    if any(severe.values()):
        choice = max((key for key in scores if severe[key]), key=lambda key: scores[key])
        return Decision(choice, f'{choice} 필요 상태가 나쁨', scores)
    choice = max(scores, key=lambda key: scores[key])
    if scores[choice] < ACTION_THRESHOLD:
        return Decision('idle', '모든 상태가 양호함', scores)
    reasons = {
        'eat': '포만감이 낮거나 먹보 성격으로 먹이 탐색 우선',
        'rest': '피로도가 높거나 잠꾸러기 성격으로 휴식 우선',
        'play': '기분이 낮거나 장난꾸러기 성격으로 놀이 우선',
    }
    return Decision(choice, reasons[choice], scores)
