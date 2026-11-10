"""Public backend facade for Pygame: all methods are UI-independent.

Writes are serialized by RLock and persisted atomically through SQLite. Every public
operation syncs real/offline time before working. UI never directly mutates state.
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


class GameRuleError(ValueError):
    """User-facing validation failure; safe to show in GUI."""


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
        self.state,self._revision=self.store.load_with_revision()
        if self.state is None:
            self.state=self._fresh_state()
            try:
                self._revision=self.store.commit(self.state,expected_revision=0)
            except SaveConflictError as exc:
                raise GameRuleError('다른 실행 중인 게임이 세이브를 생성했습니다. 다시 실행하세요.') from exc
        self._validate_loaded_save()
        self._mutate(lambda s:None) # reconcile offline work once on launch

    @staticmethod
    def _load_caps(path):
        """Validate editable, role-and-stat-specific limits before saving any game.

        JSON uses stage keys '1', '2', '3'. For each role, every individual stat
        must grow monotonically across stages. It is OK for roles to differ.
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
        """Detect wrong character catalogs before an old save is overwritten.

        Changing a character name/sprite is safe. Deleting or renaming its ID
        requires a deliberate migration because the ID is the persistent key.
        """
        if not isinstance(self.state,dict):
            raise GameRuleError('게임 저장 데이터가 손상됐습니다.')
        stored=self.state.get('animals',{})
        missing=set(stored)-set(self.characters)
        if missing:
            raise GameRuleError(f'저장된 캐릭터 ID가 현재 도감에 없습니다: {sorted(missing)}')
        if 'clock' not in self.state or 'coins' not in self.state:
            raise GameRuleError('저장 파일의 핵심 데이터가 누락됐습니다.')

    def display_info(self, key, stage=1):
        """Name and sprite for a character at an evolution stage (stage is clamped)."""
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
                'coins':300,'animals':owned,'inventory':inv,'toy_instances':[],
                'plots':[{'crop':None,'end':None,'ready':False}], 'hunts':{}, 'jobs':{},
                'battle':None,'battle_result':None,'battle_attempts':{},'last_team_roles':[],
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

    def _mutate(self, fn):
        with self._lock:
            candidate=copy.deepcopy(self.state)
            # The v2 save format had no monotonically increasing event IDs.
            # All new events are numbered, so the long-term SQLite history has
            # exactly-once insertion regardless of the 80-entry UI ring buffer.
            candidate['schema']=2
            candidate['_new_events']=[]  # never serialized; the UI ring buffer is capped at 80
            self._sync(candidate)
            result=fn(candidate)
            candidate['events']=candidate['events'][-80:]
            new_events=candidate.pop('_new_events')
            if candidate==self.state and not new_events:
                return copy.deepcopy(result)
            try:
                revision=self.store.commit(candidate,new_events,expected_revision=self._revision)
            except SaveConflictError as exc:
                raise GameRuleError('다른 게임 실행 창에서 저장 파일이 변경됐습니다. 먼저 불러오세요.') from exc
            self._revision=revision
            self.state=candidate
            return copy.deepcopy(result)

    def _read(self, fn):
        return self._mutate(fn)  # read also processes clock/events and commits resulting snapshot

    def _sync(self,s):
        clock=s['clock']
        real_now=float(self._now())
        delta=max(0.0,real_now-clock['last_real'])
        target=clock['virtual']+delta*clock['rate']
        clock['virtual']=target
        clock['last_real']=max(real_now,clock['last_real'])
        # Activities settle first at their actual scheduled timestamp so later idle rest accrues.
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
        # bounded catch-up for random weather bonuses, deterministic by fixed hash (no offline RNG spam).
        new_slot=int(target//C.BONUS_EVENT_EVERY)
        last_slot=s.get('last_bonus_slot',new_slot)
        # Only last 1000 slots processed, with cap preventing offline infinite money after many years.
        for slot in range(max(last_slot+1,new_slot-999),new_slot+1):
            digest=hashlib.sha256(f"{s['created']}:{slot}:bonus".encode()).digest()
            if int.from_bytes(digest[:4],'big')/2**32<C.BONUS_EVENT_PROBABILITY:
                s['coins']+=C.BONUS_EVENT_COINS
                self._emit(s,'random_bonus',coins=C.BONUS_EVENT_COINS)
        s['last_bonus_slot']=new_slot

    def _in_battle(self,s,key):
        return bool(s['battle'] and any(x['id']==key for x in s['battle']['player']))

    def _update_metabolism(self,a,delta):
        """Real-time fullness and mood decay, independent of what animation is playing."""
        a['fullness_accum']+=delta
        ticks=int(a['fullness_accum']//C.PASSIVE_FULLNESS_EVERY)
        a['fullness_accum']-=ticks*C.PASSIVE_FULLNESS_EVERY
        a['fullness']=bounded(a['fullness']+ticks*C.PASSIVE_FULLNESS_DELTA)
        a['mood_accum']+=delta
        ticks=int(a['mood_accum']//C.PASSIVE_MOOD_EVERY)
        a['mood_accum']-=ticks*C.PASSIVE_MOOD_EVERY
        a['mood']=bounded(a['mood']+ticks*C.PASSIVE_MOOD_DELTA)

    def _recover_idle_fatigue(self,s,a,start,delta):
        """Recover every five actual/virtual seconds, doubling recovery at night.

        Count complete 1h day/night cycles analytically for fast offline catch-up,
        checking at most 720 remainder ticks. The offset of the first tick respects
        the fractional remainder saved from the previous call.
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
        """Compatibility method: return the action label from explicit decision policy."""
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
        """Update animal state in chronological order and recalculate autonomy each minute.

        Inactive animals recover their fatigue as required by the team design, while
        play has an additional limited mood benefit. Autonomous food searching is
        a visible intention, not a free food generator. Effects are never awarded to
        an animal busy in training, hunting or battle.
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

        # Months away from the game must not require millions of behavior decisions.
        # Full metabolism/rest still elapse; the most recent 24h is replayed in detail.
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
        # 0-30 min day, 30-60 min night, repeating since world creation.
        return int((now-s['created'])//1800)%2==1

    def _is_storm(self,s,now=None):
        if now is None:now=s['clock']['virtual']
        return ((now-s['created'])%C.STORM_CYCLE)>=C.STORM_CYCLE-C.STORM_DURATION

    def _check_animal(self,s,key):
        if key not in s['animals']: raise GameRuleError('보유하지 않은 동물입니다.')
        return s['animals'][key]

    def _status_label(self,a,stat):
        value=a[stat]
        if stat=='fatigue':return 'good' if value<30 else ('normal' if value<=55 else 'bad')
        return 'bad' if value<30 else ('normal' if value<=55 else 'good')

    def _available(self,s,key):
        a=self._check_animal(s,key)
        if a['activity'] or self._in_battle(s,key): return False,'다른 활동 중입니다.'
        if a['sick']: return False,'질병 상태입니다.'
        states=[self._status_label(a,k) for k in ('fullness','fatigue','mood')]
        if 'bad' in states:return False,'상태가 나쁩니다.'
        nature=a['nature']
        if nature=='glutton' and states[0]=='normal':return False,'먹보: 포만감이 보통입니다.'
        if nature=='sleepy' and states[1]=='normal':return False,'잠꾸러기: 피로도가 보통입니다.'
        if nature=='playful' and states[2]=='normal':return False,'장난꾸러기: 기분이 보통입니다.'
        if nature=='picky' and states.count('normal')>=2:return False,'까칠: 보통 상태가 2개 이상입니다.'
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
            a['stats'][stat]=min(cap,a['stats'][stat]+amount)
            self._adjust(a,fullness=-job['cost'],mood=-job['cost'],fatigue=job['cost'])
            self._count(s,'trainings_completed')
            self._emit(s,'training_complete',animal=a['id'],stat=stat,gain=amount)
            self._disease_roll(s,a)
        elif job['kind']=='hunt':
            area=job['area']; h=C.HUNTS[area]
            # Completion produces a claimable reward, never silently duplicates.
            s['hunts'][area]['ready']=True
            self._adjust(a,fullness=-20 if h['duration']==3600 else -10,
                         mood=-10 if h['duration']==3600 else -5,
                         fatigue=35 if h['duration']==3600 else 20)
            self._count(s,'hunts_completed')
            self._emit(s,'hunt_complete',animal=a['id'],area=area)
            self._disease_roll(s,a)

    def reset_game(self,confirm=False):
        """Start new game. Destructive; caller must explicitly confirm."""
        if confirm is not True:
            raise GameRuleError('새 게임 시작은 confirm=True로 승인해야 합니다.')
        with self._lock:
            candidate=self._fresh_state()
            try:
                revision=self.store.reset(candidate,self._revision)
            except SaveConflictError as exc:
                raise GameRuleError('다른 게임 실행 창에서 저장 파일이 변경됐습니다.') from exc
            self.state=candidate
            self._revision=revision
            return {'reset':True,'coins':candidate['coins'],
                    'animals':len(candidate['animals']),'plots':len(candidate['plots'])}

    def save_game(self):
        """Explicit save button API; all other write operations are already auto-saved."""
        return self._mutate(lambda s:{'saved':True,'timestamp':s['clock']['virtual']})

    def load_game(self):
        """Load the persisted SQLite snapshot, then reconcile offline time."""
        with self._lock:
            loaded,revision=self.store.load_with_revision()
            if loaded is None:raise GameRuleError('저장된 데이터가 없습니다.')
            self.state=loaded
            self._revision=revision
            self._validate_loaded_save()
        return self.get_game_state()

    def get_game_state(self):
        def read(s):
            now=s['clock']['virtual']
            return {'coins':s['coins'],'owned_count':len(s['animals']),
                    'clock':{'timestamp':now,'night':self._is_night(s,now), 'storm':self._is_storm(s),
                             'rate':s['clock']['rate']},
                    'progress':s['progress'],'rank':s['rank'],'cook_xp':s['cook_xp'],
                    'cook_level':self._cook_level(s),'in_battle':s['battle'] is not None,
                    'plots_owned':len(s['plots']), 'recent_events':s['events'][-10:]}
        return self._read(read)

    def get_snapshot(self):
        """One consistent GUI snapshot with *one* clock reconciliation and DB write.

        The Pygame UI should call this periodically (not once per frame) and
        render only the returned dictionaries. No shared objects leak out.
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
                     'unlocked':C.STAGES[key]['order']<=s['progress']+1,
                     'cleared':key in s['cleared']}
                    for key in C.STAGE_ORDER]
            return {'schema':2,'rules_version':C.GAME_RULES_VERSION,
                    'coins':s['coins'],'clock':{'timestamp':now,
                    'night':self._is_night(s,now),'storm':self._is_storm(s,now),
                    'rate':s['clock']['rate']},
                    'progress':s['progress'],'rank':s['rank'],
                    'animals':animals,'owned_count':len(animals),
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
                            'participation':self._available(s,key)[0]})
                rows.append(row)
            return rows
        return self._read(read)

    def get_autonomous_state(self,key=None):
        """Pygame-facing autonomous AI decision and status snapshot.

        No GUI code is called here. Animations can map the returned action to sprites.
        Busy animals are marked training/hunting/battle and do not perform autonomy.
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
                'hunts':copy.deepcopy(C.HUNTS),'stages':copy.deepcopy(C.STAGES)}

    def get_inventory(self):
        return self._read(lambda s:{'stackable':dict(s['inventory']), 'toys':copy.deepcopy(s['toy_instances'])})

    def _add(self,s,item,n):
        if n<=0:return
        s['inventory'][item]=s['inventory'].get(item,0)+n

    def _take(self,s,item,n=1):
        if n<1 or s['inventory'].get(item,0)<n:raise GameRuleError('아이템 수량이 부족합니다.')
        s['inventory'][item]-=n
        if s['inventory'][item]==0:del s['inventory'][item]

    def buy_item(self,item,quantity=1):
        def fn(s):
            if item not in C.ITEMS or C.ITEMS[item]['buy'] is None:raise GameRuleError('판매하지 않는 아이템입니다.')
            if type(quantity)!=int or not 1<=quantity<=999:raise GameRuleError('수량은 1~999입니다.')
            cost=C.ITEMS[item]['buy']*quantity
            if s['coins']<cost:raise GameRuleError('코인이 부족합니다.')
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
                raise GameRuleError('판매할 수 없는 아이템입니다.')
            if type(quantity)!=int or not 1<=quantity<=999:raise GameRuleError('수량 오류')
            if C.ITEMS[item]['kind']=='toy':
                fresh=[toy for toy in s['toy_instances']
                       if toy['id']==item and toy['charges']==C.ITEMS[item]['charges']]
                if len(fresh)<quantity:raise GameRuleError('미사용 장난감이 부족합니다.')
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
                raise GameRuleError('활동 중에는 생활 아이템을 사용할 수 없습니다.')
            spec=C.ITEMS.get(item)
            if not spec:raise GameRuleError('알 수 없는 아이템입니다.')
            if spec['kind']=='toy':
                toy=next((t for t in s['toy_instances'] if t['id']==item),None)
                if not toy:raise GameRuleError('장난감이 없습니다.')
                self._adjust(a,mood=spec['mood']); toy['charges']-=1
                if toy['charges']==0:s['toy_instances'].remove(toy)
                return {'item':item,'mood':a['mood'],'charges_left':toy['charges']}
            if spec['kind']=='snack':
                self._take(s,item)
                self._adjust(a,fullness=spec['fullness'])
                return {'item':item,'fullness':a['fullness']}
            if spec['kind']=='food':
                self._take(s,item)
                # Burnt food sometimes refused; no recovery on refusal.
                refused=(spec['stars']==0 and self.rng.random()<.5)
                if not refused:
                    effect=C.FOOD_EFFECTS[spec['stars']]
                    self._adjust(a,fullness=effect['fullness'],mood=effect['mood'],fatigue=effect['fatigue'])
                return {'item':item,'refused':refused,'fullness':a['fullness'],'mood':a['mood'],'fatigue':a['fatigue']}
            if spec['kind']=='cure':
                if not a['sick']:raise GameRuleError('질병에 걸린 동물이 아닙니다.')
                self._take(s,item)
                success=self.rng.random()<spec['chance']
                if success:
                    a['sick']=False; self._adjust(a,fatigue=spec['fatigue'])
                return {'item':item,'success':success,'sick':a['sick'],'fatigue':a['fatigue']}
            raise GameRuleError('이 아이템은 여기서 사용할 수 없습니다.')
        return self._mutate(fn)

    def equip(self,key,item=None):
        def fn(s):
            a=self._check_animal(s,key)
            if a['activity'] or self._in_battle(s,key):raise GameRuleError('활동 중 장비 교체 불가')
            if item is not None and (item not in C.ITEMS or C.ITEMS[item]['kind']!='equip'):
                raise GameRuleError('장비 아이템을 선택하세요.')
            if a['equip']==item:return {'equipped':item}
            if item is not None:self._take(s,item)
            old=a['equip']
            if old:self._add(s,old,1)
            a['equip']=item
            return {'equipped':item,'returned':old}
        return self._mutate(fn)

    def hatch_egg(self,egg):
        def fn(s):
            if egg not in ('egg_basic','egg_special'):raise GameRuleError('부화 가능한 알이 아닙니다.')
            self._take(s,egg)
            rarity='special' if self.rng.random() < (.1 if egg=='egg_basic' else .6) else 'normal'
            options=[k for k,c in self.characters.items() if c['rarity']==rarity]
            # Special egg: max 20% duplicates as long as any unowned species exist.
            # If selected rarity is fully owned, prefer unowned in the other rarity;
            # rarity 60/40 target becomes approximate near a completed collection.
            if egg=='egg_special' and self.rng.random()>=.2:
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
                    'caps':caps,'next_cost':C.EVOLUTION_COST.get(stage+1) if stage<info['max_stage'] else None}
        return self._read(fn)

    def evolve(self,key):
        def fn(s):
            a=self._check_animal(s,key);info=self.characters[key];stage=a['stage']
            if a['activity'] or self._in_battle(s,key):raise GameRuleError('활동 중 진화 불가능')
            if stage>=info['max_stage']:raise GameRuleError('최종 진화 단계입니다.')
            caps=self.caps[info['role']][stage]
            if not all(a['stats'][stat]>=caps[stat] for stat in C.STATS):
                raise GameRuleError('모든 능력치를 MAX까지 훈련해야 합니다.')
            cost=C.EVOLUTION_COST[stage+1]
            if s['coins']<cost:raise GameRuleError('진화 비용이 부족합니다.')
            s['coins']-=cost
            a['stage']+=1
            self._emit(s,'evolve',animal=key,stage=a['stage'])
            return {'id':key,'stage':a['stage'],'stats':dict(a['stats']),'coins':s['coins']}
        return self._mutate(fn)

    def start_training(self,key,stat,difficulty):
        def fn(s):
            a=self._check_ready(s,key)
            if stat not in C.STATS or difficulty not in C.TRAINING:raise GameRuleError('훈련 선택이 올바르지 않습니다.')
            cap=self.caps[self.characters[key]['role']][a['stage']][stat]
            if a['stats'][stat]>=cap:raise GameRuleError('해당 능력치는 MAX입니다.')
            duration,gain,cost=C.TRAINING[difficulty]
            if a['fullness']<C.TRAINING_MIN[difficulty] or a['mood']<C.TRAINING_MIN[difficulty]:
                raise GameRuleError('훈련에 필요한 포만감 또는 기분이 부족합니다.')
            if a['fatigue']+cost>100:raise GameRuleError('훈련하기에 피로도가 너무 높습니다.')
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
            if not a['activity'] or a['activity']['kind']!='training':raise GameRuleError('훈련 중이 아닙니다.')
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
            if n>=6:raise GameRuleError('밭은 최대 6개입니다.')
            cost=C.PLOT_COSTS[n]
            if s['coins']<cost:raise GameRuleError('코인이 부족합니다.')
            s['coins']-=cost
            s['plots'].append({'crop':None,'end':None,'ready':False})
            return {'plots':len(s['plots']),'spent':cost}
        return self._mutate(fn)

    def plant_crop(self,index,crop):
        def fn(s):
            if type(index)!=int or index<0 or index>=len(s['plots']):raise GameRuleError('밭 번호 오류')
            if crop not in C.CROPS:raise GameRuleError('작물 종류 오류')
            plot=s['plots'][index]
            if plot['crop'] is not None:raise GameRuleError('이미 사용 중인 밭입니다.')
            self._take(s,'seed_'+crop)
            plot.update(crop=crop,ready=False,end=s['clock']['virtual']+C.CROP_DURATION)
            return {'plot':index,'crop':crop,'end':plot['end']}
        return self._mutate(fn)

    def harvest_crop(self,index):
        def fn(s):
            if type(index)!=int or index<0 or index>=len(s['plots']):raise GameRuleError('밭 번호 오류')
            plot=s['plots'][index]
            if not plot['ready']:raise GameRuleError('아직 수확할 수 없습니다.')
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
            if area in s['hunts']:raise GameRuleError('해당 사냥터가 사용 중입니다.')
            now=s['clock']['virtual']
            job={'kind':'hunt','area':area,'start':now,'end':now+C.HUNTS[area]['duration']}
            a['activity']=job
            s['hunts'][area]={'animal':key,'end':job['end'],'ready':False}
            a['auto_action']='hunting'
            return {'animal':key,'area':area,'end':job['end']}
        return self._mutate(fn)

    def cancel_hunting(self,area):
        def fn(s):
            if area not in s['hunts']:raise GameRuleError('파견이 없습니다.')
            hunt=s['hunts'][area]
            if hunt['ready']:
                raise GameRuleError('이미 완료된 사냥은 취소하지 않고 보상을 수령해야 합니다.')
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
            if not hunt or not hunt['ready']:raise GameRuleError('수령할 사냥 보상이 없습니다.')
            spec=C.HUNTS[area]
            self._add(s,spec['item'],spec['count'])
            del s['hunts'][area]
            return {'item':spec['item'],'count':spec['count']}
        return self._mutate(fn)

    def _cook_level(self,s):
        xp=s['cook_xp']
        return max(i+1 for i,threshold in enumerate(C.COOK_LEVEL_XP) if xp>=threshold)

    def get_recipes(self):
        def fn(s):
            level=self._cook_level(s)
            return {'level':level,'xp':s['cook_xp'],
                    'recipes':{key:{**r,'failure_chance':max(.03,C.BASE_FAIL[r['stars']]-C.COOK_FAIL_REDUCTION[level-1])}
                               for key,r in C.RECIPES.items()}}
        return self._read(fn)

    def cook(self,recipe):
        def fn(s):
            if recipe not in C.RECIPES:raise GameRuleError('없는 요리입니다.')
            r=C.RECIPES[recipe]
            for item,quantity in r['ingredients'].items():
                if s['inventory'].get(item,0)<quantity:raise GameRuleError('요리 재료가 부족합니다.')
            for item,quantity in r['ingredients'].items():self._take(s,item,quantity)
            level=self._cook_level(s)
            fail=max(.03,C.BASE_FAIL[r['stars']]-C.COOK_FAIL_REDUCTION[level-1])
            success=self.rng.random()>=fail
            obtained='food_'+recipe if success else 'burned_food'
            self._add(s,obtained,1)
            self._count(s,'cooks_attempted')
            if success:
                self._count(s,'cooks_succeeded')
                s['cook_xp']+=C.COOK_XP[r['stars']]
            return {'success':success,'item':obtained,'xp':s['cook_xp'],
                    'level':self._cook_level(s),'failure_chance':fail}
        return self._mutate(fn)

    def get_stages(self):
        def fn(s):
            return [{**C.STAGES[key],'id':key,'unlocked':C.STAGES[key]['order']<=s['progress']+1,
                     'cleared':key in s['cleared']} for key in C.STAGE_ORDER]
        return self._read(fn)

    def _stage_preview(self,s,stage):
        if stage not in C.STAGES:raise GameRuleError('없는 전투 스테이지')
        spec=C.STAGES[stage]
        attempt=s.get('battle_attempts',{}).get(stage,0)
        seed=hashlib.sha256(f"{s['created']}:{stage}:{attempt}:enemy_team".encode()).digest()
        local_rng=random.Random(int.from_bytes(seed[:8],'big'))
        if stage=='tutorial':
            roles=['tank','dealer','healer']
        else:
            roles=[local_rng.choice(list(C.ROLES)) for _ in range(3)]
            if spec['ai']=='lookahead' and s.get('last_team_roles'):
                from collections import Counter
                common=Counter(s['last_team_roles']).most_common(1)[0][0]
                element_to_counter=C.ROLE_ELEMENTS[common]
                counter_element=next(element for element,loses_to in C.ELEMENT_BEATS.items() if loses_to==element_to_counter)
                counter_role=next(role for role,element in C.ROLE_ELEMENTS.items() if element==counter_element)
                roles[0]=counter_role
                roles[1]=counter_role
        enemy_stage=3 if spec['power']>500 else (2 if spec['power']>300 else 1)
        enemies=[]
        for i,role in enumerate(roles):
            pool=sorted(k for k,c in self.characters.items()
                        if c['role']==role and c['max_stage']>=enemy_stage)
            species=local_rng.choice(pool)
            look=self.display_info(species,enemy_stage)
            enemies.append({'id':f'enemy_{i}','name':'야생 '+look['name'],'sprite':look['sprite'],
                            'species':species,'role':role,'element':C.ROLE_ELEMENTS[role],
                            'stats':{stat:spec['power'] for stat in C.STATS}})
        return {'stage':stage,'label':spec['label'],'power':spec['power'],'ai':spec['ai'],
                'enemy':enemies}

    def preview_stage(self,stage):
        """Enemy composition is stable from preview until start; changes next attempt."""
        return self._read(lambda s:self._stage_preview(s,stage))

    def start_battle(self,stage,team,prebattle_potions=None):
        def fn(s):
            if s['battle'] is not None:raise GameRuleError('이미 전투 중입니다.')
            if stage not in C.STAGES:raise GameRuleError('없는 전투 스테이지')
            spec=C.STAGES[stage]
            if spec['order']>s['progress']+1:raise GameRuleError('아직 해금되지 않았습니다.')
            if not isinstance(team,(list,tuple)) or len(team)!=3 or len(set(team))!=3:
                raise GameRuleError('서로 다른 동물 3마리를 선택해야 합니다.')
            for key in team:self._check_ready(s,key)
            potions=prebattle_potions or {}
            if not isinstance(potions,dict) or any(key not in team for key in potions):
                raise GameRuleError('포션 사용 대상 오류')
            for key,item in potions.items():
                if item not in C.ITEMS or C.ITEMS[item]['kind']!='prebattle':
                    raise GameRuleError('전투 전용 포션만 사용 가능합니다.')
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
                    'name':e['name'],'sprite':e['sprite']}
                   for e in preview['enemy']]
            s.setdefault('battle_attempts',{})[stage]=s.get('battle_attempts',{}).get(stage,0)+1
            s['last_team_roles']=[self.characters[key]['role'] for key in team]
            s['battle']={'stage':stage,'ai':spec['ai'],'player':player,'enemy':enemy,
                         'current':'player','actions':0,'round':1,'winner':None, 'log':[],
                         'consumed_potions':dict(potions),'started':s['clock']['virtual']}
            return self._battle_view(s)
        return self._mutate(fn)

    def _battle_view(self,s):
        return copy.deepcopy(s['battle'])

    def get_ai_profiles(self):
        """Used by Pygame battle difficulty descriptions; contains no save data."""
        return copy.deepcopy(B.AI_PROFILES)

    def get_battle(self):
        return self._read(lambda s:self._battle_view(s))

    def get_battle_actions(self,actor):
        """GUI can use this for buttons; no battle rules need be reimplemented in Pygame."""
        def fn(s):
            battle=s['battle']
            if battle is None or battle['current']!='player':return []
            options=B.legal_actions(battle,actor)
            if actor=='battle_bandage' and s['inventory'].get('battle_bandage',0)>0:
                options += [{'kind':'battle_item','actor':'battle_bandage','target':f['id']}
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
            if battle is None or battle['current']!='player':raise GameRuleError('플레이어 행동 차례가 아닙니다.')
            if kind=='battle_item':
                if actor!='battle_bandage':raise GameRuleError('전투 사용 아이템이 아닙니다.')
                self._take(s,'battle_bandage')
                events=B.use_battle_item(battle,actor,target)
            else:
                try:events=B.perform(battle,actor,kind,target,self.rng)
                except ValueError as exc:raise GameRuleError(str(exc)) from exc
            battle['log'].extend(events)
            self._battle_next(s)
            return {'events':events,'battle':self._battle_view(s),
                    'result':copy.deepcopy(s['battle_result']) if s['battle'] is None else None}
        return self._mutate(fn)

    def end_player_turn(self):
        def fn(s):
            battle=s['battle']
            if battle is None or battle['current']!='player':raise GameRuleError('플레이어 턴이 아닙니다.')
            B.end_turn(battle)
            self._enemy_turn(s)
            return {'battle':self._battle_view(s),'result':copy.deepcopy(s['battle_result']) if s['battle'] is None else None}
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

    def _settle_battle(self,s):
        battle=s['battle'];stage=battle['stage'];spec=C.STAGES[stage]
        win=battle['winner']=='player'; first=stage not in s['cleared']
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
                            'reward':reward,'rounds':battle['round'], 'log':battle['log'][-200:]}
        s['battle']=None
        for fighter in battle['player']:
            a=s['animals'][fighter['id']]
            a['auto_action']='idle'
            a['last_auto']=s['clock']['virtual']-C.AUTONOMOUS_EVERY
        self._emit(s,'battle_end',stage=stage,win=win,reward=reward)

    def forfeit_battle(self):
        def fn(s):
            if s['battle'] is None:raise GameRuleError('전투 중이 아닙니다.')
            s['battle']['winner']='enemy'
            self._settle_battle(s)
            return copy.deepcopy(s['battle_result'])
        return self._mutate(fn)

    def set_demo_mode(self,enabled,rate=60):
        def fn(s):
            if type(enabled)!=bool:raise GameRuleError('enabled must be bool')
            if enabled and (not isinstance(rate,(int,float)) or not 1<=rate<=3600):
                raise GameRuleError('가속 배율은 1~3600입니다.')
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
        # No extra coin rewards: only the negotiated rank prizes pay coins.
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
        """Safe to call from worker thread. Reconciles events; returns pending notifications."""
        return self._read(lambda s:copy.deepcopy(s['events'][-10:]))

    def recent_events(self):
        return self._read(lambda s:copy.deepcopy(s['events']))

    def get_event_history(self,limit=100):
        """Persistent event history for reports (beyond the most recent 80 UI events)."""
        self.tick()
        return self.store.recent_events(limit)
