from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Callable, TypeVar, Any, Tuple, List, NewType
from uuid import UUID

from src.sys.time.duration import Duration


class LogContext:
    _lock = threading.Lock()
    _logger: Dict[int, TimeLogger] = {}
    T = TypeVar('T')

    @staticmethod
    def run_logging(
            log_name: str,
            action: Callable[[], T],
            publish_report_every: Optional[Duration] = None
    ) -> T:
        thread_number = threading.get_ident()
        with LogContext._lock:
            LogContext._logger[thread_number] = TimeLogger(name=log_name, publish_report_every=publish_report_every)

        try:
            result = action()
        finally:
            with LogContext._lock:
                LogContext.logger().close()
                LogContext._logger.pop(thread_number)

        return result

    @staticmethod
    def logger() -> Optional[TimeLogger]:
        return LogContext._logger.get(threading.get_ident())

    @staticmethod
    def shift_time():
        LogContext.logger().shift_time()


Percentage = NewType('Percentage', float)
CoreNumber = NewType('CoreNumber', int)


class _Action(Enum):
    WAITING = 1
    PROCESSING = 2
    STATE_CHANGING = 3


@dataclass
class Report:
    log_name: str
    simulation_duration: Duration

    avg_core_waiting: Duration
    core_waiting_percentage: Percentage

    avg_core_processing: Duration
    core_processing_percentage: Percentage

    avg_core_state_changing: Duration
    core_state_changing_percentage: Percentage


class TimeLogger:

    def __init__(
            self,
            name: str,
            publish_report_every: Optional[Duration] = None,
            report_publisher: Callable[[Report], None] = lambda report: print(str(report))
    ):
        self._report_publisher = report_publisher
        self.name: str = name
        self._publish_report_every: Duration = publish_report_every
        self._duration: Duration = Duration(nanos=1)

        self._ticked_core: Optional[CoreNumber] = None
        self._core_to_last_action_duration: Dict[CoreNumber, Tuple[_Action, Duration]] = {}
        self._core_and_action_to_sum_duration: Dict[Tuple[CoreNumber, _Action], Tuple[Duration, int]] = {}

    def close(self):
        self._account_last_actions()

        report = self._generate_report()
        self._report_publisher(report)

    def shift_time(self):
        if self._ticked_core is not None:
            self._handle_log_action(action=_Action.STATE_CHANGING)

        self._duration = self._duration + Duration(nanos=1)

        if self._publish_report_every is not None and \
                (self._duration % self._publish_report_every) == Duration.zero():
            self._account_last_actions()

            report = self._generate_report()
            self._report_publisher(report)

    def log_core_tick(self, core_number: CoreNumber):
        if self._ticked_core is not None:
            self._handle_log_action(action=_Action.STATE_CHANGING)

        self._ticked_core = core_number

    def log_task_processing(self, name: str, identifier: UUID):
        self._log_task(identifier=identifier, action=_Action.PROCESSING)

    def log_task_waiting(self, name: str, identifier: UUID):
        self._log_task(identifier=identifier, action=_Action.WAITING)

    def _log_task(self, identifier: Any, action: _Action):
        if self._ticked_core is None:
            raise ValueError("Task ticked when core is not ticked before. "
                             "Or the task ticked more then once / a few tasks ticked after a core is ticked")
        self._handle_log_action(action)

    def _handle_log_action(self, action: _Action):
        core_number = self._ticked_core
        self._ticked_core = None

        last_action_and_its_duration = self._core_to_last_action_duration.get(core_number)
        if last_action_and_its_duration is None:
            self._core_to_last_action_duration[core_number] = action, Duration(nanos=1)
            return

        (last_action, last_action_duration) = last_action_and_its_duration

        if last_action == action:
            last_action_duration += Duration(nanos=1)
            return

        self._core_to_last_action_duration[core_number] = action, Duration(nanos=1)

        last_action_sum_duration, last_action_times = self._core_and_action_to_sum_duration.get(
            (core_number, last_action),
            (Duration(nanos=0), 1)
        )
        self._core_and_action_to_sum_duration[core_number, last_action] = \
            last_action_sum_duration + last_action_duration, last_action_times + 1

    def _account_last_actions(self):
        for core_number, (action, duration) in self._core_to_last_action_duration.items():
            action_sum_duration, action_times = self._core_and_action_to_sum_duration.get(
                (core_number, action),
                (Duration(nanos=0), 0)
            )
            self._core_and_action_to_sum_duration[core_number, action] = \
                action_sum_duration + duration, action_times + 1
        self._core_to_last_action_duration.clear()

    def _generate_report(self) -> Report:
        core_work_ratio = self._core_work_ratio()

        return Report(
            log_name=self.name,
            simulation_duration=self._duration,
            avg_core_waiting=self._avg_time_per_action(_Action.WAITING),
            core_waiting_percentage=core_work_ratio.get(_Action.WAITING, 0),
            avg_core_processing=self._avg_time_per_action(_Action.PROCESSING),
            core_processing_percentage=core_work_ratio.get(_Action.PROCESSING, 0),
            avg_core_state_changing=self._avg_time_per_action(_Action.STATE_CHANGING),
            core_state_changing_percentage=core_work_ratio.get(_Action.STATE_CHANGING, 0)
        )

    def _avg_time_per_action(self, action: _Action) -> Duration:
        avg_action_duration_per_core: List[Duration] = [
            sum_duration / times
            for (core_num, act), (sum_duration, times)
            in self._core_and_action_to_sum_duration.items()
            if act == action
        ]
        if not avg_action_duration_per_core:
            return Duration.zero()

        return Duration.avg(avg_action_duration_per_core)

    def _core_work_ratio(self) -> Dict[_Action, Percentage]:
        action_to_durations: Dict[_Action, List[Duration]] = {}
        for (core_num, action), (sum_duration, times) in self._core_and_action_to_sum_duration.items():
            action_to_durations.setdefault(action, [])
            action_to_durations[action].append(sum_duration)

        action_to_avg: Dict[_Action, Duration] = {
            action: Duration.avg(durations)
            for action, durations
            in action_to_durations.items()
        }

        hundred_percent_value: Duration = Duration.sum(action_to_avg.values())

        def sum_duration_as_percentage(act: _Action) -> Percentage:
            return Percentage(action_to_avg[act].nanos * 100 / hundred_percent_value.nanos)

        return {
            action: sum_duration_as_percentage(action)
            for action
            in action_to_avg.keys()
        }
