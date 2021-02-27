from typing import List, Optional

from src.log import LogContext, ProcessorNumber
from src.sys.thread import KernelThread
from src.sys.time.constants import thread_context_switch_overhead
from src.sys.time.duration import Duration
from src.sys.time.time import TimeAffected, TimeDelta


class Processor(TimeAffected):
    def __init__(
            self,
            processing_interval: Duration,
            yielding: bool,
            proc_number: int = -1,
            context_switch_cost: Duration = thread_context_switch_overhead()
    ):
        self.processing_interval = processing_interval
        self.number = proc_number
        self._context_switch_cost = context_switch_cost
        self._thread_pool: List[KernelThread] = []
        self._processing_slot: Optional[KernelThread] = None
        self._current_thread_processing_duration: Duration = Duration.zero()
        self._context_switch_duration: Duration = Duration.zero()
        self._yield_allowed: bool = yielding
        self._yielding: bool = False

    def assign(self, thread: KernelThread):
        self._thread_pool.append(thread)
        self._assign_first_from_pool_if_starving()

    def ticked(self, time_delta: TimeDelta):
        LogContext.logger().log_processor_tick(proc_number=ProcessorNumber(self.number))
        self._assign_first_from_pool_if_starving()

        if self._processing_slot is None:
            return

        should_yield = self._yield_allowed and (self._yielding or self._processing_slot.can_yield())
        should_finish_timeslice = self._current_thread_processing_duration >= self.processing_interval
        pool_has_more_threads = len(self._thread_pool) != 0

        if pool_has_more_threads and (should_yield or should_finish_timeslice):
            self._yielding = True
            LogContext.logger().log_overhead_tick()
            self._context_switch_duration += time_delta.duration

            if self._context_switch_duration <= self._context_switch_cost:
                return

            self._yielding = False
            self._reset_counters()
            unassigned = self._unassign_current()
            self._thread_pool.append(unassigned)
            return

        if not self._processing_slot.is_doing_system_operation():
            self._current_thread_processing_duration += time_delta.duration
        self._processing_slot.ticked(time_delta)
        self._handle_if_finished()

    def is_starving(self) -> bool:
        return self._processing_slot is None and not self._thread_pool

    def __str__(self):
        return self._as_string()

    def __repr__(self):
        return self._as_string()

    def _as_string(self):
        return f"processor({self.number})"

    def _assign_first_from_pool_if_starving(self):
        if self._processing_slot is not None:
            return
        if not self._thread_pool:
            return
        self._processing_slot = self._thread_pool.pop(0)

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

    def _unassign_current(self) -> Optional[KernelThread]:
        if self._processing_slot is None:
            return None
        self._reset_counters()
        unassigned: KernelThread = self._processing_slot
        self._processing_slot = None
        return unassigned


class ProcessorFactory:
    def __init__(self):
        self.last_processor_number = -1

    def new(
            self,
            count: int,
            processing_interval: Duration,
            yielding: bool
    ) -> List[Processor]:
        processors = []
        for i in range(count):
            self.last_processor_number += 1
            processors.append(
                Processor(
                    proc_number=self.last_processor_number,
                    processing_interval=processing_interval,
                    yielding=yielding
                )
            )
        return processors
