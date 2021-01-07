from typing import List, Optional, NewType

from src.sys.thread import Thread
from src.sys.time.time import TimeAffected, TimeDelta
from src.log import LogContext
from src.sys.time.duration import Duration


class Core(TimeAffected):
    def __init__(
            self,
            processing_interval: Duration,
            core_number: int = -1,
            context_switch_cost: Duration = Duration(nanos=20)
    ):
        self.processing_interval = processing_interval
        self.number = core_number
        self._context_switch_cost = context_switch_cost  # TODO: constants or to thread
        self._threads_pool: List[Thread] = []
        self._processing_slot: Optional[Thread] = None
        self._current_thread_processing_duration: Duration = Duration.zero()
        self._context_switch_duration: Duration = Duration.zero()

    def assign(self, thread: Thread):
        self._threads_pool.append(thread)
        self._assign_first_from_pool_if_starving()

    def ticked(self, time_delta: TimeDelta):
        LogContext.logger().log_core_tick(core_number=self.number)
        self._assign_first_from_pool_if_starving()

        if self._processing_slot is None:
            return

        if self._current_thread_processing_duration >= self.processing_interval and self._threads_pool:
            self._context_switch_duration += time_delta.duration

            if self._context_switch_duration <= self._context_switch_cost:
                return

            self._reset_counters()
            unassigned = self._unassign_current()
            self._threads_pool.append(unassigned)

        else:
            self._processing_slot.ticked(time_delta)
            self._current_thread_processing_duration += time_delta.duration
            self._handle_if_finished()

    def is_starving(self) -> bool:
        return self._processing_slot is None and not self._threads_pool

    def __str__(self):
        return self._as_string()

    def __repr__(self):
        return self._as_string()

    def _as_string(self):
        return f"Core({self.number})"

    def _assign_first_from_pool_if_starving(self):
        if self._processing_slot is not None:
            return
        if not self._threads_pool:
            return
        self._processing_slot = self._threads_pool.pop(0)

    def _reset_counters(self):
        self._context_switch_duration = Duration.zero()
        self._current_thread_processing_duration = Duration.zero()

    def _handle_if_finished(self):
        if self._processing_slot is None:
            return
        if not self._processing_slot.is_finished():
            return
        self._unassign_current()
        self._assign_first_from_pool_if_starving()

    def _unassign_current(self) -> Optional[Thread]:
        if self._processing_slot is None:
            return None
        self._reset_counters()
        unassigned: Thread = self._processing_slot
        self._processing_slot = None
        return unassigned


class CoreFactory:
    def __init__(self):
        self.last_core_number = -1

    def new(
            self,
            count: int,
            processing_interval: Duration
    ) -> List[Core]:
        cores = []
        for i in range(count):
            self.last_core_number += 1
            cores.append(Core(core_number=self.last_core_number, processing_interval=processing_interval))
        return cores
