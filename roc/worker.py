"""Optional background worker for mandatory multithreading requirement.
No Pygame calls; GUI polls the thread-safe event queue and updates itself on main thread.
"""
import queue
import threading

class GameWorker:
    def __init__(self,service,interval=1.0):
        self.service=service
        self.interval=interval
        self.events=queue.Queue(maxsize=5)
        self.stop_event=threading.Event()
        self.thread=None
        self._last_event_count=0

    def start(self):
        if self.thread and self.thread.is_alive():return
        self.stop_event.clear()
        self.thread=threading.Thread(target=self._run,name='roc-world-clock',daemon=True)
        self.thread.start()

    def _run(self):
        while not self.stop_event.wait(self.interval):
            try:
                self.service.tick()
                latest=self.service.recent_events()
                # UI is allowed to refresh based on this notification; never mutate GUI here.
                try:
                    self.events.put_nowait({'type':'world_updated','recent':latest[-5:]})
                except queue.Full:
                    pass  # GUI can query latest state on next poll; no unbounded queue growth
            except Exception as exc:
                try:self.events.put_nowait({'type':'worker_error','error':str(exc)})
                except queue.Full:pass

    def poll(self,max_events=10):
        out=[]
        for _ in range(max_events):
            try:out.append(self.events.get_nowait())
            except queue.Empty:break
        return out

    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():self.thread.join(timeout=3)
