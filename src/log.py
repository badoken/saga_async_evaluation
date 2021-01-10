from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Callable, TypeVar, Any, Tuple, List, NewType, Set
from uuid import UUID

from termcolor import colored

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
ProcessorNumber = NewType('ProcessorNumber', int)


class _Action(Enum):
    WAITING = 1
    PROCESSING = 2
    STATE_CHANGING = 3


@dataclass
class Report:
    log_name: str
    simulation_duration: Duration

    avg_proc_waiting: Duration
    proc_waiting_percentage: Percentage

    avg_proc_processing: Duration
    proc_processing_percentage: Percentage

    avg_proc_state_changing: Duration
    proc_state_changing_percentage: Percentage


class TimeLogger:
    def __init__(
            self,
            name: str,
            publish_report_every: Optional[Duration] = None,
            report_publisher: Callable[[Report], None] = lambda report: print_coloured(report)
    ):
        self._report_publisher = report_publisher
        self.name: str = name
        self._publish_report_every: Duration = publish_report_every
        self._duration: Duration = Duration(nanos=1)

        self._ticked_processor: Optional[ProcessorNumber] = None
        self._proc_to_last_action_duration: Dict[ProcessorNumber, Tuple[_Action, Duration]] = {}
        self._proc_and_action_to_sum_duration: Dict[Tuple[ProcessorNumber, _Action], Tuple[Duration, int]] = {}

    def close(self):
        self._account_last_actions()

        report = self._generate_report()
        self._report_publisher(report)

    def shift_time(self):
        if self._ticked_processor is not None:
            self._handle_log_action(action=_Action.STATE_CHANGING)

        self._duration = self._duration + Duration(nanos=1)

        if self._publish_report_every is not None and \
                (self._duration % self._publish_report_every) == Duration.zero():
            self._account_last_actions()

            report = self._generate_report()
            self._report_publisher(report)

    def log_processor_tick(self, proc_number: ProcessorNumber):
        if self._ticked_processor is not None:
            self._handle_log_action(action=_Action.STATE_CHANGING)

        self._ticked_processor = proc_number

    def log_task_processing(self, name: str, identifier: UUID):
        self._log_task(identifier=identifier, action=_Action.PROCESSING)

    def log_task_waiting(self, name: str, identifier: UUID):
        self._log_task(identifier=identifier, action=_Action.WAITING)

    def _log_task(self, identifier: Any, action: _Action):
        if self._ticked_processor is None:
            raise ValueError("Task ticked when processor is not ticked before. "
                             "Or the task ticked more then once / a few tasks ticked after a processor is ticked")
        self._handle_log_action(action)

    def _handle_log_action(self, action: _Action):
        proc_number = self._ticked_processor
        self._ticked_processor = None

        last_action_and_its_duration = self._proc_to_last_action_duration.get(proc_number)
        if last_action_and_its_duration is None:
            self._proc_to_last_action_duration[proc_number] = action, Duration(nanos=1)
            return

        (last_action, last_action_duration) = last_action_and_its_duration

        if last_action == action:
            last_action_duration += Duration(nanos=1)
            return

        self._proc_to_last_action_duration[proc_number] = action, Duration(nanos=1)

        last_action_sum_duration, last_action_times = self._proc_and_action_to_sum_duration.get(
            (proc_number, last_action),
            (Duration(nanos=0), 1)
        )
        self._proc_and_action_to_sum_duration[proc_number, last_action] = \
            last_action_sum_duration + last_action_duration, last_action_times + 1

    def _account_last_actions(self):
        for processor_number, (action, duration) in self._proc_to_last_action_duration.items():
            action_sum_duration, action_times = self._proc_and_action_to_sum_duration.get(
                (processor_number, action),
                (Duration(nanos=0), 0)
            )
            self._proc_and_action_to_sum_duration[processor_number, action] = \
                action_sum_duration + duration, action_times + 1
        self._proc_to_last_action_duration.clear()

    def _generate_report(self) -> Report:
        processor_work_ratio = self._proc_work_ratio()

        return Report(
            log_name=self.name,
            simulation_duration=self._duration,
            avg_proc_waiting=self._avg_time_per_action(_Action.WAITING),
            proc_waiting_percentage=processor_work_ratio.get(_Action.WAITING, 0),
            avg_proc_processing=self._avg_time_per_action(_Action.PROCESSING),
            proc_processing_percentage=processor_work_ratio.get(_Action.PROCESSING, 0),
            avg_proc_state_changing=self._avg_time_per_action(_Action.STATE_CHANGING),
            proc_state_changing_percentage=processor_work_ratio.get(_Action.STATE_CHANGING, 0)
        )

    def _avg_time_per_action(self, action: _Action) -> Duration:
        avg_action_duration_per_proc: List[Duration] = [
            sum_duration / times
            for (proc_num, act), (sum_duration, times)
            in self._proc_and_action_to_sum_duration.items()
            if act == action
        ]
        if not avg_action_duration_per_proc:
            return Duration.zero()

        return Duration.avg(avg_action_duration_per_proc)

    def _proc_work_ratio(self) -> Dict[_Action, Percentage]:
        action_to_durations: Dict[_Action, List[Duration]] = {}
        for (proc_num, action), (sum_duration, times) in self._proc_and_action_to_sum_duration.items():
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


_available_colours: Set[str] = {"grey", "red", "green", "yellow", "blue", "magenta", "cyan", "white"}
_assigned_colours: Dict[str, str] = {}


def print_coloured(report: Report):
    colour = _assigned_colours.get(report.log_name)
    if colour is None:
        colour = _available_colours.pop()
        _assigned_colours[report.log_name] = colour

    print(colored(str(report), color=colour))
