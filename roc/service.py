"""Pygame에서 사용하는 백엔드 진입점이며 모든 메서드는 UI와 독립적이다.

상태 변경은 RLock으로 순서대로 처리하고 SQLite에 원자적으로 저장한다.
모든 공개 작업은 실행 전에 실제 시간과 오프라인 진행을 반영한다.
UI는 내부 상태를 직접 변경하지 않는다.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import random
import threading
import time
from pathlib import Path
from typing import Any
from . import config as C
from . import battle as B
from . import autonomy as AUTO
from .store import SQLiteStore, SaveConflictError


_UNSET = object()


class GameRuleError(ValueError):
    """GUI에 표시할 수 있는 게임 규칙 검증 오류."""


def bounded(x,low=0,high=100):
    return max(low,min(high,x))


class GameService:
    def __init__(self, save_path='saves/game.db', character_path=None, now=None, rng=None, cap_path=None):
        self._lock=threading.RLock()
        self._now=now if now is not None else time.time
        self.rng=rng if rng is not None else random.Random()
        self.store=SQLiteStore(save_path)
        if character_path is None:
            character_path=Path(__file__).resolve().parent.parent/'data'/'characters.json'
        self.characters=json.loads(Path(character_path).read_text(encoding='utf-8'))
        if cap_path is None:
            cap_path=Path(__file__).resolve().parent.parent/'data'/'role_caps.json'
        self.caps=self._load_caps(cap_path)
        self._validate_catalog()
        self.enemies=self._load_enemies(Path(__file__).resolve().parent.parent/'data'/'enemies.json')
        self.state,self._revision=self.store.load_with_revision()
        if self.state is None:
            self.state=self._fresh_state()
            try:
                self._revision=self.store.commit(self.state,expected_revision=0)
            except SaveConflictError as exc:
                raise GameRuleError('다른 게임에서 세이브 생성됨 · 다시 실행') from exc
        self._validate_loaded_save()
        # 빠르게·시연 모드의 배속은 현재 실행에만 적용한다. 오프라인 시간은
        # 이전 실행이 가속 중에 끝났더라도 1배속으로 정산한다.
        self.state['clock']['rate']=1.0
        self._mutate(lambda s:None) # 실행 시 오프라인 진행을 한 번 정산한다.

    @staticmethod
    def _load_caps(path):
        """게임을 저장하기 전에 역할·능력치·진화 단계별 상한 설정을 검증한다.

        JSON의 단계 키는 '1', '2', '3'이다. 각 역할의 모든 능력치 상한은
        진화 단계가 올라갈수록 감소하지 않아야 하며 역할별 값은 달라도 된다.
        """
        raw=json.loads(Path(path).read_text(encoding='utf-8'))
        caps={}
        if set(raw)!=set(C.ROLES):
            raise ValueError('role_caps.json must define dealer/tank/healer')
        for role,stages in raw.items():
            if set(stages)!=set(('1','2','3')):
                raise ValueError('role_caps.json must define stages 1, 2, 3')
            caps[role]={}
            previous={stat:0 for stat in C.STATS}
            for stage in (1,2,3):
                values=stages[str(stage)]
                if set(values)!=set(C.STATS):
                    raise ValueError('role_caps.json must define all four stats')
                if any(type(value)!=int or value<=0 for value in values.values()):
                    raise ValueError('caps must be positive integers')
                if any(values[stat]<previous[stat] for stat in C.STATS):
                    raise ValueError('caps cannot decrease after evolution')
                caps[role][stage]=dict(values)
                previous=values
        return caps

    @staticmethod
    def _load_enemies(path):
        """저장 데이터를 변경하기 전에 공통 적 이미지 목록을 불러온다."""
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        if (not isinstance(data,dict)
            or not isinstance(data.get('minions'),list)
            or not isinstance(data.get('bosses'),list)):
            raise ValueError('enemies.json must define minions and bosses lists')
        seen=set()
        stages=set()
        minion_roles=set()
        for group in ('minions','bosses'):
            for entry in data[group]:
                if not isinstance(entry,dict):raise ValueError('invalid enemy entry')
                key=entry.get('id')
                role=entry.get('role')
                if not isinstance(key,str) or not key or key in seen:
                    raise ValueError('invalid or duplicate enemy ID')
                seen.add(key)
                if role not in C.ROLES or entry.get('element')!=C.ROLE_ELEMENTS[role]:
                    raise ValueError('enemy role/element mismatch')
                if any(not isinstance(entry.get(field),str) or not entry[field].strip()
                       for field in ('name','sprite')):
                    raise ValueError('enemy name and sprite must be nonempty strings')
                if group=='bosses':
                    stage=entry.get('stage')
                    if (not isinstance(stage,str) or stage not in C.STAGES
                        or stage in stages or entry.get('boss') is not True):
                        raise ValueError('each stage must have exactly one boss')
                    stages.add(stage)
                else:
                    if entry.get('boss',False):raise ValueError('minion cannot be a boss')
                    minion_roles.add(role)
        if stages!=set(C.STAGES) or minion_roles!=set(C.ROLES):
            raise ValueError('enemy catalog must cover every stage and minion role')
        return data

    def _validate_catalog(self):
        if len(self.characters)!=30: raise ValueError('catalog must contain exactly 30 species')
        seen=set()
        for key, entry in self.characters.items():
            if key in seen or entry['id']!=key: raise ValueError('invalid character ID')
            seen.add(key)
            if entry['role'] not in C.ROLES or entry['rarity'] not in ('normal','special'):
                raise ValueError('invalid role/rarity')
            if entry['element']!=C.ROLE_ELEMENTS[entry['role']]: raise ValueError('role/element mismatch')
            if entry['max_stage']!=(2 if entry['rarity']=='normal' else 3): raise ValueError('stage mismatch')
            if set(entry['base_stats'])!=set(C.STATS) or any(type(x)!=int or x<1 for x in entry['base_stats'].values()):
                raise ValueError('invalid base stats')
            for stat,value in entry['base_stats'].items():
                if value>self.caps[entry['role']][1][stat]: raise ValueError('base stats exceed stage 1 caps')

    def _validate_loaded_save(self):
        """이전 저장을 덮어쓰기 전에 동물 목록이 호환되는지 확인한다.

        동물 이름이나 이미지는 변경할 수 있지만 ID는 영구 저장 키이다.
        ID를 삭제하거나 바꾸려면 저장 데이터를 명시적으로 이전해야 한다.
        """
        if not isinstance(self.state,dict):
            raise GameRuleError('저장 데이터 손상')
        stored=self.state.get('animals',{})
        missing=set(stored)-set(self.characters)
        if missing:
            raise GameRuleError(f'도감에 없는 저장 동물: {sorted(missing)}')
        if 'clock' not in self.state or 'coins' not in self.state:
            raise GameRuleError('저장 파일 핵심 데이터 누락')

    def display_info(self, key, stage=1):
        """진화 단계에 맞는 이름과 이미지 경로를 반환하고 단계는 유효 범위로 제한한다."""
        info=self.characters[key]
        names=info.get('stage_names') or [info['name']]
        sprites=info.get('stage_sprites') or [info.get('sprite')]
        i=max(0,min(int(stage or 1),len(names))-1)
        return {'name':names[i],'sprite':sprites[min(i,len(sprites)-1)],
                'species':info.get('species',info['name'])}

    def _new_animal(self, key, now):
        info=self.characters[key]
        return {'id':key,'stage':1,'stats':dict(info['base_stats']), 'nature':self.rng.choice(C.NATURES),
                'mood':80,'fullness':80,'fatigue':0,'sick':False,'equip':None,'activity':None,
                'last_tick':now,'fullness_accum':0,'mood_accum':0,'rest_accum':0,
                'play_accum':0,'last_auto':now,'auto_action':'idle',
                'auto_reason':'모든 상태가 양호함', 'auto_priorities':{}}

    def _fresh_state(self):
        now=float(self._now())
        starter={role: next(key for key,c in self.characters.items() if c['rarity']=='normal' and c['role']==role)
                 for role in C.ROLES}
        owned={key:self._new_animal(key,now) for key in starter.values()}
        inv={'snack':3}
        return {'schema':2,'event_seq':0,'created':now,'clock':{'virtual':now,'last_real':now,'rate':1.0},
                'coins':300,'animals':owned,'yard':[], 'last_saved':now,
                'inventory':inv,'toy_instances':[],
                'plots':[{'crop':None,'end':None,'ready':False}], 'hunts':{}, 'jobs':{},
                'battle':None,'battle_result':None,'battle_attempts':{},'last_team_roles':[], 'last_team':[],
                'progress':-1,'cleared':[], 'rank':'none',
                'claimed_ranks':[],'cook_xp':0,'last_bonus_slot':int(now//C.BONUS_EVENT_EVERY),
                'events':[], 'achievements':[], 'counters':{}}

    def _count(self,s,key,amount=1):
        s.setdefault('counters',{})[key]=s.setdefault('counters',{}).get(key,0)+amount

    def _emit(self,s,kind,**kwargs):
        s['event_seq']=s.get('event_seq',0)+1
        event={'seq':s['event_seq'],'type':kind,'time':s['clock']['virtual'],**kwargs}
        s['events'].append(event)
        if '_new_events' in s:
            s['_new_events'].append(event)
        s['events']=s['events'][-80:]

    def _mutate(self, fn, *, force_save=False):
        with self._lock:
            candidate=copy.deepcopy(self.state)
            # 이전 저장에는 출전 동물 목록이 없으므로 역할 정보만으로 ID를 복구하지 않는다.
            candidate.setdefault('last_team',[])
            # 마당 선택이 없는 이전 저장은 빈 목록으로 시작하고 GUI가 빈칸을 채운다.
            # 이전 버전의 6마리 선택은 표시 순서대로 앞의 5마리만 유지한다.
            # 선택에서 제외된 동물도 보유 목록에서는 삭제하지 않는다.
            if 'yard' not in candidate:
                candidate['yard']=[]
            yard=candidate['yard']
            if (not isinstance(yard,list) or len(yard)>6
                or any(type(k)!=str or k not in candidate['animals'] for k in yard)
                or len(set(yard))!=len(yard)):
                raise GameRuleError('저장된 마당 동물 정보 오류')
            if len(yard)>C.YARD_MAX_ANIMALS:
                candidate['yard']=yard[:C.YARD_MAX_ANIMALS]
            # 이전 v2 저장에는 계속 증가하는 이벤트 ID가 없었다.
            # 새 이벤트에는 모두 번호를 부여해 GUI의 최근 80개 기록과 무관하게
            # SQLite 장기 기록에 각 이벤트를 한 번씩만 추가한다.
            candidate['schema']=2
            candidate['_new_events']=[]  # 저장하지 않는 임시 목록이며 GUI 기록은 최대 80개이다.
            self._sync(candidate)
            # 자동 저장을 포함한 실제 시각을 Unix 초로 기록하며 가속된 가상 시간은 쓰지 않는다.
            # API 응답과 저장 내용이 일치하도록 응답 생성 전에 시각을 준비한다.
            # 작업이나 저장이 실패하면 준비한 시각도 반영하지 않는다.
            candidate['last_saved']=float(self._now())
            result=fn(candidate)
            candidate['events']=candidate['events'][-80:]
            new_events=candidate.pop('_new_events')
            if not force_save and candidate==self.state and not new_events:
                return copy.deepcopy(result)
            try:
                revision=self.store.commit(candidate,new_events,expected_revision=self._revision)
            except SaveConflictError as exc:
                raise GameRuleError('다른 게임에서 저장 파일 변경됨 · 먼저 불러오기') from exc
            self._revision=revision
            self.state=candidate
            return copy.deepcopy(result)

    def _read(self, fn):
        return self._mutate(fn)  # 조회도 시간·이벤트를 처리하고 변경된 상태를 저장한다.

    def _sync(self,s):
        clock=s['clock']
        real_now=float(self._now())
        delta=max(0.0,real_now-clock['last_real'])
        target=clock['virtual']+delta*clock['rate']
        clock['virtual']=target
        clock['last_real']=max(real_now,clock['last_real'])
        # 활동은 예정된 종료 시각에 먼저 정산해 이후의 휴식 시간도 반영한다.
        for animal in s['animals'].values():
            job=animal['activity']
            if job and job['end']<=target:
                self._tick_animal(s,animal,job['end'],busy=True)
                self._finish_animal_job(s,animal,job)
                animal['activity']=None
                animal['auto_action']='idle'
                animal['auto_reason']='활동 완료, 자율 행동 재평가 예정'
                animal['last_auto']=job['end']-C.AUTONOMOUS_EVERY
            self._tick_animal(s,animal,target,busy=animal['activity'] is not None or self._in_battle(s,animal['id']))
        for plot in s['plots']:
            if plot['crop'] is not None and not plot['ready'] and target>=plot['end']:
                plot['ready']=True
                self._emit(s,'crop_ready',crop=plot['crop'])
        # 무작위 보너스는 고정 해시로 정산해 오프라인 구간의 반복 난수 추첨을 피한다.
        new_slot=int(target//C.BONUS_EVENT_EVERY)
        last_slot=s.get('last_bonus_slot',new_slot)
        # 최근 1000개 구간만 처리해 장기간 미접속에 따른 보너스 누적을 제한한다.
        for slot in range(max(last_slot+1,new_slot-999),new_slot+1):
            digest=hashlib.sha256(f"{s['created']}:{slot}:bonus".encode()).digest()
            if int.from_bytes(digest[:4],'big')/2**32<C.BONUS_EVENT_PROBABILITY:
                s['coins']+=C.BONUS_EVENT_COINS
                self._emit(s,'random_bonus',coins=C.BONUS_EVENT_COINS)
        s['last_bonus_slot']=new_slot

    def _in_battle(self,s,key):
        return bool(s['battle'] and any(x['id']==key for x in s['battle']['player']))

    def _update_metabolism(self,a,delta):
        """화면 애니메이션과 관계없이 경과 시간에 따라 포만감과 기분을 감소시킨다."""
        a['fullness_accum']+=delta
        ticks=int(a['fullness_accum']//C.PASSIVE_FULLNESS_EVERY)
        a['fullness_accum']-=ticks*C.PASSIVE_FULLNESS_EVERY
        a['fullness']=bounded(a['fullness']+ticks*C.PASSIVE_FULLNESS_DELTA)
        a['mood_accum']+=delta
        ticks=int(a['mood_accum']//C.PASSIVE_MOOD_EVERY)
        a['mood_accum']-=ticks*C.PASSIVE_MOOD_EVERY
        a['mood']=bounded(a['mood']+ticks*C.PASSIVE_MOOD_DELTA)

    def _recover_idle_fatigue(self,s,a,start,delta):
        """실제·가상 시간 5초마다 피로도를 회복하며 밤에는 회복량이 두 배이다.

        오프라인 진행을 빠르게 정산하도록 완전한 1시간 낮밤 주기는 계산으로 처리하고
        나머지 구간만 최대 720회 확인한다. 첫 회복 시점에는 이전 호출에서 남은
        소수 단위 시간을 반영한다.
        """
        prev=a['rest_accum']
        total=prev+delta
        steps=int(total//C.REST_EVERY)
        a['rest_accum']=total-steps*C.REST_EVERY
        if not steps:return
        first=start+(C.REST_EVERY-prev if prev>0 else C.REST_EVERY)
        cycle_ticks=int(3600//C.REST_EVERY)
        full_cycles,remainder=divmod(steps,cycle_ticks)
        nighttime=full_cycles*(cycle_ticks//2)
        nighttime+=sum(self._is_night(s,first+i*C.REST_EVERY) for i in range(remainder))
        a['fatigue']=bounded(a['fatigue']-(steps+nighttime))

    def _select_auto(self,a):
        """호환성을 위해 자율 행동 판단 규칙에서 선택한 행동 이름을 반환한다."""
        return AUTO.evaluate(a).action

    def _switch_auto(self,s,a,at):
        decision=AUTO.evaluate(a)
        old=a.get('auto_action','idle')
        a['auto_action']=decision.action
        a['auto_reason']=decision.reason
        a['auto_priorities']=decision.priorities
        a['last_auto']=at
        if old!=decision.action:
            a['play_accum']=0
            self._emit(s,'autonomous_action',animal=a['id'],
                       action=decision.action,previous=old,
                       reason=decision.reason,at=at)

    def _tick_animal(self,s,a,until,busy):
        """시간 순서대로 동물 상태를 갱신하고 매분 자율 행동을 다시 판단한다.

        활동하지 않는 동물은 기본 규칙에 따라 피로도를 회복하고
        혼자 놀기는 정해진 한도 안에서 기분을 추가로 회복한다.
        먹이 탐색은 의도를 표시하며 먹이를 무료로 만들지는 않는다.
        훈련·사냥·전투 중인 동물에는 자율 행동 효과를 적용하지 않는다.
        """
        start=a['last_tick']
        if until<=start:return
        a.setdefault('auto_reason','')
        a.setdefault('auto_priorities',{})
        if busy:
            self._update_metabolism(a,until-start)
            a['last_tick']=until
            a['rest_accum']=0
            a['play_accum']=0
            a['last_auto']=until
            if a.get('activity'):
                a['auto_action']=a['activity']['kind'] if a['activity']['kind']!='hunt' else 'hunting'
                a['auto_reason']='다른 활동 진행 중: 자율 행동 일시 중지'
            elif self._in_battle(s,a['id']):
                a['auto_action']='battle'
                a['auto_reason']='전투 중: 자율 행동 일시 중지'
            return

        # 다음 분의 자율 행동 판단 전에 자연 회복으로 피로도가 낮아지더라도
        # 강제 휴식은 바로 다음 GUI 상태에 표시해야 한다.
        if (a['fatigue'] > AUTO.FORCED_REST_FATIGUE_THRESHOLD
                and a.get('auto_action') != 'rest'):
            self._switch_auto(s,a,start)

        # 몇 달간 미접속했더라도 자율 행동을 수백만 번 판단하지 않도록 한다.
        # 전체 시간의 상태 감소·휴식은 반영하고 최근 24시간의 행동만 상세히 재현한다.
        if until-start>C.AUTONOMOUS_OFFLINE_DETAIL_WINDOW:
            early=until-C.AUTONOMOUS_OFFLINE_DETAIL_WINDOW
            self._update_metabolism(a,early-start)
            self._recover_idle_fatigue(s,a,start,early-start)
            a['last_tick']=early
            a['auto_action']='idle'
            a['play_accum']=0
            a['last_auto']=early-C.AUTONOMOUS_EVERY

        while a['last_tick']+1e-8<until:
            now=a['last_tick']
            next_decision=a['last_auto']+C.AUTONOMOUS_EVERY
            if next_decision<=now+1e-8:
                self._switch_auto(s,a,now)
                continue
            target=min(until,next_decision)
            delta=target-now
            self._update_metabolism(a,delta)
            self._recover_idle_fatigue(s,a,now,delta)
            if a['auto_action']=='play':
                a['play_accum']+=delta
                count=int(a['play_accum']//C.AUTONOMOUS_PLAY_EVERY)
                a['play_accum']-=count*C.AUTONOMOUS_PLAY_EVERY
                if count and a['mood']<C.AUTONOMOUS_PLAY_MOOD_CAP:
                    a['mood']=min(C.AUTONOMOUS_PLAY_MOOD_CAP,
                                  a['mood']+count*C.AUTONOMOUS_PLAY_MOOD_GAIN)
            else:
                a['play_accum']=0
            a['last_tick']=target
            if target>=next_decision-1e-8:
                self._switch_auto(s,a,target)

    def _is_night(self,s,now):
        # 게임 생성 시점부터 0~30분은 낮, 30~60분은 밤으로 반복한다.
        return int((now-s['created'])//1800)%2==1

    def _clock_view(self, s, now):
        """GUI용 시계이며 게임의 하루는 가상 시간 60분으로 낮과 밤이 각각 30분이다.

        첫날은 06:00에 시작하고 실제·가상 시간 2.5초마다 화면의 시각이 1분 지난다.
        다음 06:00에 날짜가 증가하므로 날짜는 완료된 낮밤 주기를 나타낸다.
        기존 절대 시각 timestamp와 밤·태풍 여부 필드는 유지한다.
        """
        elapsed = max(0.0, now - s['created'])
        day = 1 + int(elapsed // 3600)
        game_minute = (6 * 60 + int((elapsed % 3600) * 1440 // 3600)) % 1440
        return {'timestamp': now, 'day': day,
                'time': f'{game_minute // 60:02d}:{game_minute % 60:02d}',
                'night': self._is_night(s, now),
                'storm': self._is_storm(s, now), 'rate': s['clock']['rate']}

    def _is_storm(self,s,now=None):
        if now is None:now=s['clock']['virtual']
        return ((now-s['created'])%C.STORM_CYCLE)>=C.STORM_CYCLE-C.STORM_DURATION

    def _check_animal(self,s,key):
        if key not in s['animals']: raise GameRuleError('보유하지 않은 동물')
        return s['animals'][key]

    def _status_label(self,a,stat):
        value=a[stat]
        if stat=='fatigue':return 'good' if value<30 else ('normal' if value<=55 else 'bad')
        return 'bad' if value<30 else ('normal' if value<=55 else 'good')

    def _animal_status(self,a):
        """게임 참여 조건과 같은 경곗값으로 GUI용 3단계 상태를 반환한다."""
        return {stat:self._status_label(a,stat) for stat in ('fullness','mood','fatigue')}

    def _available(self,s,key):
        a=self._check_animal(s,key)
        if a['activity'] or self._in_battle(s,key): return False,'다른 활동 중'
        if a['sick']: return False,'아파서 활동 불가'
        states=[self._status_label(a,k) for k in ('fullness','fatigue','mood')]
        if 'bad' in states:return False,'상태 나쁨'
        nature=a['nature']
        if nature=='glutton' and states[0]=='normal':return False,'먹보: 좋은 포만감 필요'
        if nature=='sleepy' and states[1]=='normal':return False,'잠꾸러기: 더 휴식 필요'
        if nature=='playful' and states[2]=='normal':return False,'장난꾸러기: 좋은 기분 필요'
        if nature=='picky' and states.count('normal')>=2:return False,'까칠: 보통 상태 2개 이상'
        return True,''

    def can_participate(self,key):
        return self._read(lambda s: {'ok':self._available(s,key)[0], 'reason':self._available(s,key)[1]})

    def _check_ready(self,s,key):
        ok,reason=self._available(s,key)
        if not ok:raise GameRuleError(reason)
        return s['animals'][key]

    def _adjust(self,a,fullness=0,mood=0,fatigue=0):
        a['fullness']=bounded(a['fullness']+fullness)
        a['mood']=bounded(a['mood']+mood)
        a['fatigue']=bounded(a['fatigue']+fatigue)

    def _disease_roll(self,s,a):
        if self.rng.random()<C.DISEASE_CHANCE:
            a['sick']=True
            self._emit(s,'disease',animal=a['id'])

    def _finish_animal_job(self,s,a,job):
        if job['kind']=='training':
            stat=job['stat']
            cap=self.caps[self.characters[a['id']]['role']][a['stage']][stat]
            amount=job['gain']
            before=a['stats'][stat]
            a['stats'][stat]=min(cap,a['stats'][stat]+amount)
            self._adjust(a,fullness=-job['cost'],mood=-job['cost'],fatigue=job['cost'])
            self._count(s,'trainings_completed')
            self._emit(s,'training_complete',animal=a['id'],stat=stat,gain=a['stats'][stat]-before)
            self._disease_roll(s,a)
        elif job['kind']=='hunt':
            area=job['area']; h=C.HUNTS[area]
            # 완료 시 수령 가능한 보상만 준비하고 같은 보상을 중복 지급하지 않는다.
            s['hunts'][area]['ready']=True
            self._adjust(a,**h['completion_effects'])
            self._count(s,'hunts_completed')
            self._emit(s,'hunt_complete',animal=a['id'],area=area)
            self._disease_roll(s,a)

    def reset_game(self,confirm=False):
        """기존 진행을 지우고 새 게임을 시작하므로 호출자가 명시적으로 확인해야 한다."""
        if confirm is not True:
            raise GameRuleError('새 게임 시작 확인 필요')
        with self._lock:
            candidate=self._fresh_state()
            try:
                revision=self.store.reset(candidate,self._revision)
            except SaveConflictError as exc:
                raise GameRuleError('다른 게임에서 저장 파일 변경됨') from exc
            self.state=candidate
            self._revision=revision
            return {'reset':True,'coins':candidate['coins'],
                    'animals':len(candidate['animals']),'plots':len(candidate['plots'])}

    def save_game(self):
        """저장 버튼용 API이며 다른 상태 변경 작업도 모두 자동 저장한다."""
        return self._mutate(lambda s:{'saved':True,'timestamp':s['clock']['virtual'],
                                      'last_saved':s['last_saved']}, force_save=True)

    def load_game(self):
        """SQLite에 저장된 상태를 불러온 뒤 오프라인 진행을 정산한다."""
        with self._lock:
            loaded,revision=self.store.load_with_revision()
            if loaded is None:raise GameRuleError('저장 데이터 없음')
            self.state=loaded
            self._revision=revision
            self._validate_loaded_save()
            self.state['clock']['rate']=1.0
        return self.get_game_state()

    def get_game_state(self):
        def read(s):
            now=s['clock']['virtual']
            return {'coins':s['coins'],'owned_count':len(s['animals']),
                    'clock':self._clock_view(s,now),
                    'progress':s['progress'],'rank':s['rank'],
                    'yard':list(s['yard']), 'yard_max':C.YARD_MAX_ANIMALS,
                    'last_team':list(s['last_team']), 'last_saved':s['last_saved'],
                    'cook_xp':s['cook_xp'],
                    'cook_level':self._cook_level(s),'in_battle':s['battle'] is not None,
                    'plots_owned':len(s['plots']), 'recent_events':s['events'][-10:]}
        return self._read(read)

    def get_snapshot(self):
        """시간 정산과 DB 저장을 각각 한 번만 수행해 일관된 GUI 상태를 반환한다.

        Pygame UI는 매 프레임이 아닌 일정 주기로 호출하고 반환된 사전만 그린다.
        내부의 공유 객체는 외부에 노출하지 않는다.
        """
        def fn(s):
            now=s['clock']['virtual']
            animals=[]
            for key,a in s['animals'].items():
                info=self.characters[key]
                row=copy.deepcopy(a)
                ok,reason=self._available(s,key)
                row.update(**self.display_info(key,a['stage']),role=info['role'],element=info['element'],
                           rarity=info['rarity'],
                           max_stage=info['max_stage'],
                           caps=copy.deepcopy(self.caps[info['role']][a['stage']]),
                           effective_stats=B.stats_for(a,a['equip']),
                           status=self._animal_status(a),
                           participation=ok,participation_reason=reason)
                if a['activity']:
                    row['remaining_seconds']=max(0,a['activity']['end']-now)
                animals.append(row)
            plots=[]
            for index, plot in enumerate(s['plots']):
                copy_plot=copy.deepcopy(plot)
                copy_plot['index']=index
                copy_plot['remaining_seconds']=(max(0,plot['end']-now)
                    if plot['crop'] and not plot['ready'] else 0)
                plots.append(copy_plot)
            hunts={area:{**copy.deepcopy(job),'remaining_seconds':max(0,job['end']-now)}
                   for area,job in s['hunts'].items()}
            stages=[{**C.STAGES[key],'id':key,
                     'ai_description':B.AI_PROFILES[C.STAGES[key]['ai']]['summary'],
                     'unlocked':C.STAGES[key]['order']<=s['progress']+1,
                     'cleared':key in s['cleared']}
                    for key in C.STAGE_ORDER]
            return {'schema':2,'rules_version':C.GAME_RULES_VERSION,
                    'coins':s['coins'],'clock':self._clock_view(s,now),
                    'progress':s['progress'],'rank':s['rank'],
                    'animals':animals,'owned_count':len(animals),
                    'yard':list(s['yard']), 'yard_max':C.YARD_MAX_ANIMALS,
                    'last_team':list(s['last_team']), 'last_saved':s['last_saved'],
                    'inventory':{'stackable':dict(s['inventory']),
                                 'toys':copy.deepcopy(s['toy_instances'])},
                    'plots':plots,'hunts':hunts,'stages':stages,
                    'battle':copy.deepcopy(s['battle']),
                    'battle_result':copy.deepcopy(s['battle_result']),
                    'cook':{'xp':s['cook_xp'],'level':self._cook_level(s)},
                    'events':copy.deepcopy(s['events'][-15:])}
        return self._read(fn)

    def get_animals(self):
        def read(s):
            rows=[]
            for key,a in s['animals'].items():
                info=self.characters[key]
                row=copy.deepcopy(a)
                row.update(self.display_info(key,a['stage']))
                row.update({'role':info['role'],'element':info['element'],
                            'rarity':info['rarity'],'max_stage':info['max_stage'],
                            'caps':copy.deepcopy(self.caps[info['role']][a['stage']]),
                            'effective_stats':B.stats_for(a,a['equip']),
                            'status':self._animal_status(a),
                            'participation':self._available(s,key)[0]})
                rows.append(row)
            return rows
        return self._read(read)

    def get_yard_animals(self):
        """전체 보유 목록이 아닌 마당에 표시하도록 선택한 동물 ID만 반환한다."""
        return self._read(lambda s:{'keys':list(s['yard']),'max':C.YARD_MAX_ANIMALS})

    def set_yard_animals(self,keys):
        """보유 동물 0~5마리를 표시 순서대로 선택하고 SQLite에 자동 저장한다.

        GUI의 마당 선택에만 영향을 주며 훈련·전투·상태 감소·오프라인 진행·
        자율 행동에는 영향을 주지 않는다.
        """
        def fn(s):
            if type(keys) is not list:
                raise GameRuleError('마당 동물 목록 필요')
            if len(keys)>C.YARD_MAX_ANIMALS:
                raise GameRuleError(f'마당은 최대 {C.YARD_MAX_ANIMALS}마리')
            if any(type(key)!=str or key not in s['animals'] for key in keys):
                raise GameRuleError('보유 동물만 마당 배치 가능')
            if len(set(keys))!=len(keys):
                raise GameRuleError('같은 동물 중복 배치 불가')
            s['yard']=list(keys)
            return {'yard':list(s['yard']),'count':len(keys),'max':C.YARD_MAX_ANIMALS}
        return self._mutate(fn)

    def get_autonomous_state(self,key=None):
        """Pygame에서 사용할 자율 행동 판단과 현재 상태를 반환한다.

        GUI 코드는 호출하지 않으며 화면에서는 반환된 행동에 이미지를 연결할 수 있다.
        활동 중인 동물은 training/hunting/battle로 표시하고 자율 행동은 수행하지 않는다.
        """
        def fn(s):
            selected=[self._check_animal(s,key)] if key is not None else list(s['animals'].values())
            result=[]
            for a in selected:
                action=a.get('auto_action','idle')
                result.append({'id':a['id'], 'action':action,
                               'label':AUTO.ACTION_LABELS.get(action,action),
                               'reason':a.get('auto_reason',''),
                               'priorities':copy.deepcopy(a.get('auto_priorities',{})),
                               'nature':a['nature'], 'sick':a['sick'],
                               'fullness':a['fullness'], 'mood':a['mood'],
                               'fatigue':a['fatigue'],
                               'next_evaluation_seconds':max(0,C.AUTONOMOUS_EVERY-(s['clock']['virtual']-a['last_auto']))
                               if a['activity'] is None and not self._in_battle(s,a['id']) else None})
            return result[0] if key is not None else result
        return self._read(fn)

    def get_catalog(self):
        return copy.deepcopy(self.characters)

    def get_pokedex(self):
        def fn(s):
            return [{'id':key,**self.display_info(key,s['animals'][key]['stage'] if key in s['animals'] else 1),
                     'role':info['role'],'rarity':info['rarity'],
                     'element':info['element'],'owned':key in s['animals'],
                     'stage':s['animals'][key]['stage'] if key in s['animals'] else None,
                     'stats':dict(s['animals'][key]['stats']) if key in s['animals'] else None}
                    for key,info in self.characters.items()]
        return self._read(fn)

    def get_shop_catalog(self):
        return copy.deepcopy(C.ITEMS)

    def get_rules(self):
        return {'training':copy.deepcopy(C.TRAINING),'caps':copy.deepcopy(self.caps),
                'evolution_cost':dict(C.EVOLUTION_COST),'plot_costs':list(C.PLOT_COSTS),
                'hunts':copy.deepcopy(C.HUNTS),'stages':copy.deepcopy(C.STAGES),
                'crops':{'duration_seconds':C.CROP_DURATION, 'yield':C.CROP_YIELD},
                'hatching':copy.deepcopy(C.HATCHING),
                'disease_probability':C.DISEASE_CHANCE,
                'yard_max':C.YARD_MAX_ANIMALS,
                'cooking':{'xp_per_star':dict(C.COOK_XP),
                           'level_thresholds':list(C.COOK_LEVEL_XP),
                           'miss_rescue_by_level':list(C.COOK_MISS_RESCUE_BY_LEVEL),
                           'miss_rescue_max_star':C.COOK_MISS_RESCUE_MAX_STAR,
                           'judgments':list(C.COOK_JUDGMENTS),
                           'grades':list(C.COOK_GRADES),
                           'perfect_multiplier':C.COOK_PERFECT_MULTIPLIER,
                           'timing':copy.deepcopy(C.COOK_TIMING)}}

    def get_inventory(self):
        return self._read(lambda s:{'stackable':dict(s['inventory']), 'toys':copy.deepcopy(s['toy_instances'])})

    def _add(self,s,item,n):
        if n<=0:return
        s['inventory'][item]=s['inventory'].get(item,0)+n

    def _take(self,s,item,n=1):
        if n<1 or s['inventory'].get(item,0)<n:raise GameRuleError('아이템 수량 부족')
        s['inventory'][item]-=n
        if s['inventory'][item]==0:del s['inventory'][item]

    def buy_item(self,item,quantity=1):
        def fn(s):
            if item not in C.ITEMS or C.ITEMS[item]['buy'] is None:raise GameRuleError('구매할 수 없는 아이템')
            if type(quantity)!=int or not 1<=quantity<=999:raise GameRuleError('수량은 1~999개')
            cost=C.ITEMS[item]['buy']*quantity
            if s['coins']<cost:raise GameRuleError('코인 부족')
            s['coins']-=cost
            self._count(s,'items_purchased',quantity)
            if C.ITEMS[item]['kind']=='toy':
                for _ in range(quantity):
                    s['toy_instances'].append({'id':item,'charges':C.ITEMS[item]['charges']})
            else:self._add(s,item,quantity)
            return {'item':item,'quantity':quantity,'spent':cost,'coins':s['coins']}
        return self._mutate(fn)

    def sell_item(self,item,quantity=1):
        def fn(s):
            if item not in C.ITEMS or C.ITEMS[item]['sell'] is None:
                raise GameRuleError('판매 불가 아이템')
            if type(quantity)!=int or not 1<=quantity<=999:raise GameRuleError('수량 오류')
            if C.ITEMS[item]['kind']=='toy':
                fresh=[toy for toy in s['toy_instances']
                       if toy['id']==item and toy['charges']==C.ITEMS[item]['charges']]
                if len(fresh)<quantity:raise GameRuleError('미사용 장난감 부족')
                for toy in fresh[:quantity]:s['toy_instances'].remove(toy)
            else:
                self._take(s,item,quantity)
            gain=C.ITEMS[item]['sell']*quantity
            s['coins']+=gain
            return {'item':item,'quantity':quantity,'earned':gain,'coins':s['coins']}
        return self._mutate(fn)

    def use_item(self,item,key):
        def fn(s):
            a=self._check_animal(s,key)
            if a['activity'] is not None or self._in_battle(s,key):
                raise GameRuleError('활동 중 아이템 사용 불가')
            spec=C.ITEMS.get(item)
            if not spec:raise GameRuleError('알 수 없는 아이템')
            if spec['kind']=='toy':
                toy=next((t for t in s['toy_instances'] if t['id']==item),None)
                if not toy:raise GameRuleError('장난감 없음')
                self._adjust(a,mood=spec['mood']); toy['charges']-=1
                if toy['charges']==0:s['toy_instances'].remove(toy)
                return {'item':item,'mood':a['mood'],'charges_left':toy['charges']}
            if spec['kind']=='snack':
                self._take(s,item)
                self._adjust(a,fullness=spec['fullness'])
                return {'item':item,'fullness':a['fullness']}
            if spec['kind']=='food':
                self._take(s,item)
                # 탄 음식은 일정 확률로 거부하며 거부하면 상태가 회복되지 않는다.
                refused=(spec['stars']==0 and self.rng.random()<.5)
                if not refused:
                    effect=spec['effects']
                    self._adjust(a,fullness=effect['fullness'],mood=effect['mood'],fatigue=effect['fatigue'])
                return {'item':item,'refused':refused,'fullness':a['fullness'],'mood':a['mood'],'fatigue':a['fatigue']}
            if spec['kind']=='cure':
                if not a['sick']:raise GameRuleError('아프지 않은 동물')
                self._take(s,item)
                success=self.rng.random()<spec['chance']
                if success:
                    a['sick']=False; self._adjust(a,fatigue=spec['fatigue'])
                return {'item':item,'success':success,'sick':a['sick'],'fatigue':a['fatigue']}
            raise GameRuleError('여기서 사용할 수 없는 아이템')
        return self._mutate(fn)

    def equip(self,key,item=None):
        def fn(s):
            a=self._check_animal(s,key)
            if a['activity'] or self._in_battle(s,key):raise GameRuleError('활동 중 장비 교체 불가')
            if item is not None and (item not in C.ITEMS or C.ITEMS[item]['kind']!='equip'):
                raise GameRuleError('장비 선택 필요')
            if a['equip']==item:return {'equipped':item}
            if item is not None:self._take(s,item)
            old=a['equip']
            if old:self._add(s,old,1)
            a['equip']=item
            return {'equipped':item,'returned':old}
        return self._mutate(fn)

    def hatch_egg(self,egg):
        def fn(s):
            if egg not in C.HATCHING:raise GameRuleError('부화할 수 없는 알')
            self._take(s,egg)
            spec=C.HATCHING[egg]
            rarity='special' if self.rng.random() < spec['special_probability'] else 'normal'
            options=[k for k,c in self.characters.items() if c['rarity']==rarity]
            # 특수 알은 미보유 종이 남아 있으면 중복 확률을 최대 20%로 제한한다.
            # 선택한 등급의 모든 종을 보유했다면 다른 등급의 미보유 종을 우선한다.
            # 따라서 도감 완성에 가까워지면 등급별 60:40 비율은 달라질 수 있다.
            if egg=='egg_special' and self.rng.random()>=spec['duplicate_probability_cap']:
                unowned=[key for key in options if key not in s['animals']]
                if not unowned:
                    unowned=[key for key in self.characters if key not in s['animals']]
                if unowned:options=unowned
            key=self.rng.choice(options)
            duplicate=key in s['animals']
            if not duplicate:s['animals'][key]=self._new_animal(key,s['clock']['virtual'])
            self._emit(s,'hatch',animal=key,duplicate=duplicate)
            return {'id':key,**self.display_info(key,1),'duplicate':duplicate,'refund':0,'owned':len(s['animals'])}
        return self._mutate(fn)

    def get_evolution_status(self,key):
        def fn(s):
            a=self._check_animal(s,key);info=self.characters[key]
            stage=a['stage'];caps=self.caps[info['role']][stage]
            ready=(stage<info['max_stage'] and all(a['stats'][stat]>=caps[stat] for stat in C.STATS))
            return {'ready':ready,'stage':stage,'max_stage':info['max_stage'],
                    'role':info['role'], 'stats':dict(a['stats']),
                    'caps':copy.deepcopy(caps),
                    'remaining':{stat:max(0,caps[stat]-a['stats'][stat]) for stat in C.STATS},
                    'next_caps':copy.deepcopy(self.caps[info['role']][stage+1])
                      if stage<info['max_stage'] else None,
                    'next_cost':C.EVOLUTION_COST.get(stage+1) if stage<info['max_stage'] else None}
        return self._read(fn)

    def evolve(self,key):
        def fn(s):
            a=self._check_animal(s,key);info=self.characters[key];stage=a['stage']
            if a['activity'] or self._in_battle(s,key):raise GameRuleError('활동 중 진화 불가')
            if stage>=info['max_stage']:raise GameRuleError('최종 진화 단계')
            caps=self.caps[info['role']][stage]
            if not all(a['stats'][stat]>=caps[stat] for stat in C.STATS):
                raise GameRuleError('모든 능력치 MAX 필요')
            cost=C.EVOLUTION_COST[stage+1]
            if s['coins']<cost:raise GameRuleError('진화 코인 부족')
            s['coins']-=cost
            a['stage']+=1
            self._emit(s,'evolve',animal=key,stage=a['stage'])
            return {'id':key,'stage':a['stage'],'stats':dict(a['stats']),'coins':s['coins'],
                    **self.display_info(key,a['stage'])}
        return self._mutate(fn)

    def start_training(self,key,stat,difficulty):
        def fn(s):
            a=self._check_ready(s,key)
            if stat not in C.STATS or difficulty not in C.TRAINING:raise GameRuleError('훈련 선택 오류')
            cap=self.caps[self.characters[key]['role']][a['stage']][stat]
            if a['stats'][stat]>=cap:raise GameRuleError('이미 MAX 능력치')
            duration,gain,cost=C.TRAINING[difficulty]
            if a['fullness']<C.TRAINING_MIN[difficulty] or a['mood']<C.TRAINING_MIN[difficulty]:
                raise GameRuleError('훈련할 포만감·기분 부족')
            if a['fatigue']+cost>100:raise GameRuleError('피로가 높아 훈련 불가')
            if a['fatigue']>=C.FATIGUE_TRAINING_HALF_THRESHOLD:gain=math.floor(gain*.5+.5)
            now=s['clock']['virtual']
            a['activity']={'kind':'training','stat':stat,'difficulty':difficulty,'start':now,
                           'end':now+duration,'gain':gain*(2 if self._is_storm(s,now) else 1), 'cost':cost}
            a['auto_action']='training'
            return {'animal':key,'end':now+duration,'stat':stat,'expected_gain':a['activity']['gain']}
        return self._mutate(fn)

    def cancel_training(self,key):
        def fn(s):
            a=self._check_animal(s,key)
            if not a['activity'] or a['activity']['kind']!='training':raise GameRuleError('훈련 중 아님')
            a['activity']=None
            a['auto_action']='idle'
            a['last_auto']=s['clock']['virtual']-C.AUTONOMOUS_EVERY
            return {'cancelled':True,'reward':0}
        return self._mutate(fn)

    def get_plots(self):
        return self._read(lambda s:copy.deepcopy(s['plots']))

    def expand_plot(self):
        def fn(s):
            n=len(s['plots'])
            if n>=6:raise GameRuleError('밭은 최대 6개')
            cost=C.PLOT_COSTS[n]
            if s['coins']<cost:raise GameRuleError('코인 부족')
            s['coins']-=cost
            s['plots'].append({'crop':None,'end':None,'ready':False})
            return {'plots':len(s['plots']),'spent':cost}
        return self._mutate(fn)

    def plant_crop(self,index,crop):
        def fn(s):
            if type(index)!=int or index<0 or index>=len(s['plots']):raise GameRuleError('밭 번호 오류')
            if crop not in C.CROPS:raise GameRuleError('작물 종류 오류')
            plot=s['plots'][index]
            if plot['crop'] is not None:raise GameRuleError('사용 중인 밭')
            self._take(s,'seed_'+crop)
            plot.update(crop=crop,ready=False,end=s['clock']['virtual']+C.CROP_DURATION)
            return {'plot':index,'crop':crop,'end':plot['end']}
        return self._mutate(fn)

    def harvest_crop(self,index):
        def fn(s):
            if type(index)!=int or index<0 or index>=len(s['plots']):raise GameRuleError('밭 번호 오류')
            plot=s['plots'][index]
            if not plot['ready']:raise GameRuleError('아직 수확 불가')
            crop=plot['crop']
            self._add(s,crop,C.CROP_YIELD)
            self._count(s,'crops_harvested',C.CROP_YIELD)
            plot.update(crop=None,end=None,ready=False)
            return {'crop':crop,'count':C.CROP_YIELD}
        return self._mutate(fn)

    def get_hunts(self):
        return self._read(lambda s:{'areas':copy.deepcopy(C.HUNTS),'active':copy.deepcopy(s['hunts'])})

    def start_hunting(self,key,area):
        def fn(s):
            a=self._check_ready(s,key)
            if area not in C.HUNTS:raise GameRuleError('사냥터 오류')
            if area in s['hunts']:raise GameRuleError('사용 중인 사냥터')
            now=s['clock']['virtual']
            job={'kind':'hunt','area':area,'start':now,'end':now+C.HUNTS[area]['duration']}
            a['activity']=job
            s['hunts'][area]={'animal':key,'end':job['end'],'ready':False}
            a['auto_action']='hunting'
            return {'animal':key,'area':area,'end':job['end']}
        return self._mutate(fn)

    def cancel_hunting(self,area):
        def fn(s):
            if area not in s['hunts']:raise GameRuleError('진행 중인 사냥 없음')
            hunt=s['hunts'][area]
            if hunt['ready']:
                raise GameRuleError('완료된 사냥 · 보상 먼저 받기')
            a=self._check_animal(s,hunt['animal'])
            if a['activity'] and a['activity'].get('area')==area:
                a['activity']=None
                a['auto_action']='idle'
                a['last_auto']=s['clock']['virtual']-C.AUTONOMOUS_EVERY
            del s['hunts'][area]
            return {'cancelled':True,'items':0}
        return self._mutate(fn)

    def collect_hunt(self,area):
        def fn(s):
            hunt=s['hunts'].get(area)
            if not hunt or not hunt['ready']:raise GameRuleError('받을 사냥 보상 없음')
            spec=C.HUNTS[area]
            self._add(s,spec['item'],spec['count'])
            del s['hunts'][area]
            return {'item':spec['item'],'count':spec['count']}
        return self._mutate(fn)

    def _cook_level(self,s):
        xp=s['cook_xp']
        return max(i+1 for i,threshold in enumerate(C.COOK_LEVELS) if xp>=threshold)

    def _cook_rescue_chance(self,stars,level):
        if stars>C.COOK_MISS_RESCUE_MAX_STAR:
            return 0.0
        return C.COOK_MISS_RESCUE_BY_LEVEL[level-1]

    def get_recipes(self):
        def fn(s):
            level=self._cook_level(s)
            return {'level':level,'xp':s['cook_xp'],
                    'recipes':{key:{**r,'miss_rescue_chance':self._cook_rescue_chance(r['stars'],level),
                                    'miss_failure_chance':1.0-self._cook_rescue_chance(r['stars'],level),
                                    'travel_seconds':C.COOK_TIMING['travel_seconds_by_star'][r['stars']],
                                    'regular_item':'food_'+key,'perfect_item':'food_perfect_'+key}
                               for key,r in C.RECIPES.items()}}
        return self._read(fn)

    def cook(self,recipe,judgment=_UNSET,*,grade=_UNSET):
        """별도 실패 추첨 없이 GUI에서 측정한 타이밍 판정으로 요리 결과를 계산한다.

        기본 입력은 judgment='perfect'/'good'/'miss'이다. 기존 호출과의 호환을 위해
        grade=와 첫 글자가 대문자인 판정도 허용한다. 판정 생략 시 이전 시연처럼
        good을 적용하며 GUI는 실제 측정한 판정을 항상 전달해야 한다.
        xp는 이번 시도의 보상이고 total_xp는 누적 요리 경험치이다.
        """
        if judgment is not _UNSET and grade is not _UNSET:
            raise GameRuleError('요리 판정은 한 번만 전달')
        selected=judgment if judgment is not _UNSET else grade
        if selected is _UNSET:
            selected='good'
        if not isinstance(selected,str) or selected.lower() not in C.COOK_JUDGMENTS:
            raise GameRuleError('요리 판정 오류')
        selected=selected.lower()

        def fn(s):
            if not isinstance(recipe,str) or recipe not in C.RECIPES:
                raise GameRuleError('없는 요리')
            r=C.RECIPES[recipe]
            for item,quantity in r['ingredients'].items():
                if s['inventory'].get(item,0)<quantity:raise GameRuleError('요리 재료 부족')
            for item,quantity in r['ingredients'].items():self._take(s,item,quantity)
            level=self._cook_level(s)
            rescue_chance=self._cook_rescue_chance(r['stars'],level)
            fail=1.0-rescue_chance if selected=='miss' else 0.0
            rescued=(selected=='miss' and rescue_chance>0.0
                     and self.rng.random()<rescue_chance)
            success=selected!='miss' or rescued
            if not success:
                obtained='burned_food'; result='failure'; outcome='burnt'
            elif selected=='perfect':
                obtained='food_perfect_'+recipe; result='great_success'; outcome='great'
            else:
                obtained='food_'+recipe; result='success'
                outcome='rescued' if rescued else 'success'
            self._add(s,obtained,1)
            self._count(s,'cooks_attempted')
            gained=0
            if success:
                self._count(s,'cooks_succeeded')
                if not rescued:
                    gained=C.COOK_XP[r['stars']]
                    s['cook_xp']+=gained
            return {'success':success,'judgment':selected,'outcome':outcome,
                    'grade':selected.title(),'result':result,'item':obtained,
                    'effect_multiplier':C.ITEMS[obtained]['effect_multiplier'],
                    'effects':dict(C.ITEMS[obtained]['effects']),
                    'xp':gained,'xp_gained':gained,'total_xp':s['cook_xp'],
                    'level':self._cook_level(s),
                    'failure_chance':fail,'miss_rescue_chance':rescue_chance,
                    'rescued':rescued}
        return self._mutate(fn)

    def get_stages(self):
        def fn(s):
            return [{**C.STAGES[key],'id':key,
                     'ai_description':B.AI_PROFILES[C.STAGES[key]['ai']]['summary'],
                     'unlocked':C.STAGES[key]['order']<=s['progress']+1,
                     'cleared':key in s['cleared']} for key in C.STAGE_ORDER]
        return self._read(fn)

    def _stage_preview(self,s,stage):
        if stage not in C.STAGES:raise GameRuleError('없는 전투 스테이지')
        spec=C.STAGES[stage]
        attempt=s.get('battle_attempts',{}).get(stage,0)
        seed=hashlib.sha256(f"{s['created']}:{stage}:{attempt}:enemy_team".encode()).digest()
        local_rng=random.Random(int.from_bytes(seed[:8],'big'))
        boss=next(b for b in self.enemies['bosses'] if b['stage']==stage)
        if stage=='tutorial':
            roles=['dealer','healer']
        else:
            roles=[local_rng.choice(list(C.ROLES)) for _ in range(2)]
            if spec['ai']=='lookahead' and s.get('last_team_roles'):
                from collections import Counter
                common=Counter(s['last_team_roles']).most_common(1)[0][0]
                element_to_counter=C.ROLE_ELEMENTS[common]
                counter_element=next(element for element,loses_to in C.ELEMENT_BEATS.items() if loses_to==element_to_counter)
                counter_role=next(role for role,element in C.ROLE_ELEMENTS.items() if element==counter_element)
                roles[0]=counter_role
                roles[1]=counter_role
        selected=[boss]
        for role in roles:
            pool=sorted((e for e in self.enemies['minions'] if e['role']==role),key=lambda e:e['id'])
            # 같은 역할의 졸개 둘을 고를 때는 서로 다른 종을 우선하고 시드 선택을 유지한다.
            unused=[e for e in pool if e['id'] not in {x['id'] for x in selected}]
            selected.append(local_rng.choice(unused or pool))
        enemies=[]
        for i,entry in enumerate(selected):
            enemies.append({'id':f'enemy_{i}','name':entry['name'],'sprite':entry['sprite'],
                            'species':entry['id'],'boss':i==0,
                            'role':entry['role'],'element':entry['element'],
                            'stats':{stat:spec['power'] for stat in C.STATS}})
        return {'stage':stage,'label':spec['label'],'power':spec['power'],'ai':spec['ai'],
                'ai_description':B.AI_PROFILES[spec['ai']]['summary'],
                'enemy':enemies}

    def preview_stage(self,stage):
        """적 구성은 미리보기부터 전투 시작까지 유지하고 다음 도전에서 바뀐다."""
        return self._read(lambda s:self._stage_preview(s,stage))

    def start_battle(self,stage,team,prebattle_potions=None):
        def fn(s):
            if s['battle'] is not None:raise GameRuleError('이미 전투 중')
            if stage not in C.STAGES:raise GameRuleError('없는 전투 스테이지')
            spec=C.STAGES[stage]
            if spec['order']>s['progress']+1:raise GameRuleError('아직 잠긴 스테이지')
            if not isinstance(team,(list,tuple)) or len(team)!=3 or len(set(team))!=3:
                raise GameRuleError('서로 다른 동물 3마리 필요')
            for key in team:self._check_ready(s,key)
            potions=prebattle_potions or {}
            if not isinstance(potions,dict) or any(key not in team for key in potions):
                raise GameRuleError('포션 사용 대상 오류')
            for key,item in potions.items():
                if item not in C.ITEMS or C.ITEMS[item]['kind']!='prebattle':
                    raise GameRuleError('전투 전용 포션만 사용 가능')
            for item in potions.values():self._take(s,item)
            player=[]
            for key in team:
                a=s['animals'][key]; info=self.characters[key]
                fighter=B.make_fighter(key,'player',info['role'],info['element'],a['stage'],
                                       B.stats_for(a,a['equip'],potions.get(key)))
                look=self.display_info(key,a['stage'])
                fighter.update(name=look['name'],sprite=look['sprite'])
                player.append(fighter)
            preview=self._stage_preview(s,stage)
            enemy=[{**B.make_fighter(e['id'],'enemy',e['role'],e['element'],3 if spec['power']>500 else (2 if spec['power']>300 else 1),e['stats']),
                    'name':e['name'],'sprite':e['sprite'],'species':e['species'],'boss':e['boss']}
                   for e in preview['enemy']]
            s.setdefault('battle_attempts',{})[stage]=s.get('battle_attempts',{}).get(stage,0)+1
            s['last_team_roles']=[self.characters[key]['role'] for key in team]
            s['last_team']=list(team)
            s['battle']={'stage':stage,'ai':spec['ai'],'player':player,'enemy':enemy,
                         'current':'player','actions':0,'round':1,'winner':None, 'log':[],
                         'consumed_potions':dict(potions),'started':s['clock']['virtual']}
            return self._battle_view(s)
        return self._mutate(fn)

    def _battle_view(self,s):
        return copy.deepcopy(s['battle'])

    def get_ai_profiles(self):
        """Pygame의 전투 난이도 설명에 사용하며 저장 데이터는 포함하지 않는다."""
        return copy.deepcopy(B.AI_PROFILES)

    def get_battle(self):
        return self._read(lambda s:self._battle_view(s))

    def get_battle_actions(self,actor):
        """GUI 버튼에 사용할 수 있는 행동을 반환하므로 화면에서 전투 규칙을 다시 구현할 필요가 없다."""
        def fn(s):
            battle=s['battle']
            if battle is None or battle['current']!='player':return []
            options=B.legal_actions(battle,actor)
            if actor=='battle_bandage' and s['inventory'].get('battle_bandage',0)>0:
                options += [{'kind':'battle_item','actor':'battle_bandage','target':f['id'],
                             'amount':B.battle_item_heal_amount('battle_bandage',f)}
                            for f in battle['player'] if B.alive(f) and f['hp']<f['stats']['hp']
                            if battle['actions']<B.max_actions(battle)]
            return options
        return self._read(fn)

    def get_active_jobs(self):
        def fn(s):
            now=s['clock']['virtual']
            training=[]
            for animal in s['animals'].values():
                if animal['activity']:
                    job=copy.deepcopy(animal['activity'])
                    job.update(animal=animal['id'],remaining_seconds=max(0,job['end']-now))
                    training.append(job)
            return {'animal_jobs':training, 'plots':copy.deepcopy(s['plots']),
                    'hunts':copy.deepcopy(s['hunts'])}
        return self._read(fn)

    def get_last_battle_result(self):
        return self._read(lambda s:copy.deepcopy(s['battle_result']))

    def battle_action(self,actor,kind='attack',target=None):
        def fn(s):
            battle=s['battle']
            if battle is None or battle['current']!='player':raise GameRuleError('아직 내 차례 아님')
            log_start=len(battle['log'])
            if kind=='battle_item':
                if actor!='battle_bandage':raise GameRuleError('전투용 아이템 아님')
                self._take(s,'battle_bandage')
                events=B.use_battle_item(battle,actor,target)
            else:
                try:events=B.perform(battle,actor,kind,target,self.rng)
                except ValueError as exc:raise GameRuleError(str(exc)) from exc
            battle['log'].extend(events)
            self._battle_next(s)
            return {'events':events,'turn_events':copy.deepcopy(battle['log'][log_start:]),
                    'battle':self._battle_view(s),
                    'result':copy.deepcopy(s['battle_result']) if s['battle'] is None else None}
        return self._mutate(fn)

    def end_player_turn(self):
        def fn(s):
            battle=s['battle']
            if battle is None or battle['current']!='player':raise GameRuleError('아직 내 차례 아님')
            log_start=len(battle['log'])
            B.end_turn(battle)
            self._enemy_turn(s)
            return {'turn_events':copy.deepcopy(battle['log'][log_start:]),
                    'battle':self._battle_view(s),'result':copy.deepcopy(s['battle_result']) if s['battle'] is None else None}
        return self._mutate(fn)

    def _battle_next(self,s):
        battle=s['battle']
        if battle['winner'] is not None:
            self._settle_battle(s);return
        if battle['actions']>=B.max_actions(battle):
            B.end_turn(battle)
            self._enemy_turn(s)

    def _enemy_turn(self,s):
        battle=s['battle']
        if not battle:return
        limit=B.max_actions(battle)
        for _ in range(limit):
            decision=B.choose_ai_decision(battle,battle['ai'],self.rng)
            if decision is None:break
            move=decision['action']
            battle['log'].append({'type':'ai_decision',**decision})
            events=B.perform(battle,move['actor'],move['kind'],move['target'],self.rng)
            battle['log'].extend(events)
            if battle['winner'] is not None:break
        if battle['winner'] is not None:self._settle_battle(s)
        else:B.end_turn(battle)

    def _settle_battle(self,s,*,reason=None):
        battle=s['battle'];stage=battle['stage'];spec=C.STAGES[stage]
        win=battle['winner']=='player'; first=stage not in s['cleared']
        end_reason=reason or ('victory' if win else 'defeat')
        reward=0
        self._count(s,'battles_won' if win else 'battles_lost')
        if win:
            if spec['mode']=='normal':reward=spec['reward']*(2 if self._is_storm(s) else 1)
            elif first:reward=spec['reward']
            s['coins']+=reward
            if first:
                s['cleared'].append(stage)
                s['progress']=max(s['progress'],spec['order'])
                if spec['mode']=='rank':s['rank']=stage;s['claimed_ranks'].append(stage)
        for fighter in battle['player']:
            a=s['animals'][fighter['id']]
            if stage!='tutorial':
                self._adjust(a,fullness=-10 if win else -20,mood=-5 if win else -15,
                             fatigue=30 if win else 100)
                self._disease_roll(s,a)
        if win and first and stage=='tutorial':self._add(s,'snack',2)
        s['battle_result']={'stage':stage,'winner':battle['winner'],'win':win,'first_clear':first,
                            'end_reason':end_reason,
                            'reward':reward,'rounds':battle['round'], 'log':battle['log'][-200:]}
        s['battle']=None
        for fighter in battle['player']:
            a=s['animals'][fighter['id']]
            a['auto_action']='idle'
            a['last_auto']=s['clock']['virtual']-C.AUTONOMOUS_EVERY
        self._emit(s,'battle_end',stage=stage,win=win,reward=reward,end_reason=end_reason)

    def forfeit_battle(self):
        def fn(s):
            if s['battle'] is None:raise GameRuleError('전투 중 아님')
            s['battle']['winner']='enemy'
            self._settle_battle(s,reason='forfeit')
            return copy.deepcopy(s['battle_result'])
        return self._mutate(fn)

    def set_demo_mode(self,enabled,rate=60):
        def fn(s):
            if type(enabled)!=bool:raise GameRuleError('배속 켜기·끄기 값 오류')
            if enabled and (not isinstance(rate,(int,float)) or not 1<=rate<=3600):
                raise GameRuleError('배속은 1~3600배')
            s['clock']['rate']=float(rate) if enabled else 1.0
            return {'demo':enabled,'rate':s['clock']['rate']}
        return self._mutate(fn)

    def _achievement_flags(self,s):
        owned=len(s['animals'])
        counters=s.get('counters',{})
        ranks=('bronze','silver','gold','diamond')
        return {
            'first_win':counters.get('battles_won',0)>=1 or bool(s['cleared']),
            'first_training':counters.get('trainings_completed',0)>=1,
            'first_hunt':counters.get('hunts_completed',0)>=1,
            'first_crop':counters.get('crops_harvested',0)>=1,
            'first_cooking':counters.get('cooks_succeeded',0)>=1 or s['cook_xp']>0,
            'cooking_master':self._cook_level(s)==5,
            'pokedex_10':owned>=10,
            'pokedex_complete':owned==len(self.characters),
            'first_evolution':any(a['stage']>=2 for a in s['animals'].values()),
            'fully_evolved':any(a['stage']==self.characters[a['id']]['max_stage']
                                for a in s['animals'].values()),
            'max_stats':any(all(a['stats'][k]>=self.caps[self.characters[a['id']]['role']][a['stage']][k]
                                 for k in C.STATS) for a in s['animals'].values()),
            'champion':s['rank']=='diamond',
            **{'rank_'+r:r in s.get('claimed_ranks',[]) for r in ranks},
        }

    def get_achievements(self):
        return self._read(lambda s:self._achievement_flags(s))

    def get_achievement_details(self):
        # 추가 코인 보상은 없으며 등급 달성 보상만 코인을 지급한다.
        labels={
          'first_win':'첫 승리', 'first_training':'첫 훈련 완료',
          'first_hunt':'첫 자동 사냥 완료','first_crop':'첫 수확',
          'first_cooking':'첫 요리 성공','cooking_master':'요리 마스터',
          'pokedex_10':'도감 10종 수집','pokedex_complete':'도감 완성',
          'first_evolution':'첫 진화','fully_evolved':'최종 진화 동물 보유',
          'max_stats':'모든 능력치 MAX 달성 동물 보유',
          'champion':'다이아몬드 챔피언',
          'rank_bronze':'브론즈 승급','rank_silver':'실버 승급',
          'rank_gold':'골드 승급','rank_diamond':'다이아몬드 승급',
        }
        def fn(s):
            flags=self._achievement_flags(s)
            return [{'id':code,'label':labels[code],'achieved':achieved}
                    for code,achieved in flags.items()]
        return self._read(fn)

    def get_statistics(self):
        return self._read(lambda s:copy.deepcopy(s.get('counters',{})))

    def tick(self):
        """월드 스레드에서 안전하게 호출해 이벤트를 정산하고 알림을 반환한다."""
        return self._read(lambda s:copy.deepcopy(s['events'][-10:]))

    def recent_events(self):
        return self._read(lambda s:copy.deepcopy(s['events']))

    def get_event_history(self,limit=100):
        """보고서용 영구 이벤트 기록을 반환하며 GUI의 최근 80개 제한보다 오래된 기록도 포함한다."""
        self.tick()
        return self.store.recent_events(limit)
