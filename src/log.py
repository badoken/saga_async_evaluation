from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from random import shuffle
from typing import Dict, Optional, Callable, TypeVar, Any, Tuple, List, NewType, Set, Collection, Union, ValuesView
from uuid import UUID

from termcolor import colored

from src.sys.time.duration import Duration


class LogContext:
    _logger: Dict[int, TimeLogger] = {}
    T = TypeVar('T')

    @staticmethod
    def run_logging(
            log_name: str,
            action: Callable[[], T],
            publish_report_every: Optional[Duration] = None
    ) -> T:
        thread_number = threading.get_ident()
        LogContext._logger[thread_number] = TimeLogger(name=log_name, publish_report_every=publish_report_every)

        try:
            result = action()
        finally:
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
    OVERHEAD = 3


@dataclass
class Report:
    log_name: str
    simulation_duration: Duration

    avg_processor_task_handling: Duration
    processor_task_handling_percentage: Percentage

    avg_processor_waiting: Duration
    processor_waiting_percentage: Percentage

    avg_processor_overhead_work: Duration
    processor_overhead_work_percentage: Percentage


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
        self._duration: Duration = Duration(micros=1)

        self._ticked_processor: Optional[ProcessorNumber] = None
        self._proc_to_last_action_duration: Dict[ProcessorNumber, Tuple[_Action, Duration]] = {}
        self._proc_and_action_to_sum_duration: Dict[Tuple[ProcessorNumber, _Action], Duration] = {}

    def close(self):
        self._account_last_actions()

        report = self._generate_report()
        self._report_publisher(report)

    def shift_time(self):
        if self._ticked_processor is not None:
            self._handle_log_action(action=_Action.WAITING)

        self._duration = self._duration + Duration(micros=1)

        if self._publish_report_every is not None and \
                (self._duration % self._publish_report_every) == Duration.zero():
            self._account_last_actions()

            report = self._generate_report()
            self._report_publisher(report)

    def log_processor_tick(self, proc_number: ProcessorNumber):
        if self._ticked_processor is not None:
            self._handle_log_action(action=_Action.WAITING)

        self._ticked_processor = proc_number

    def log_task_processing(self, name: str, identifier: UUID):
        self._log_task(identifier=identifier, action=_Action.PROCESSING)

    def log_overhead_tick(self):
        self._log_task(identifier="overhead", action=_Action.OVERHEAD)

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
            self._proc_to_last_action_duration[proc_number] = action, Duration(micros=1)
            return

        (last_action, last_action_duration) = last_action_and_its_duration

        if last_action == action:
            last_action_duration += Duration(micros=1)
            return

        self._proc_to_last_action_duration[proc_number] = action, Duration(micros=1)

        last_action_sum_duration = self._proc_and_action_to_sum_duration.get(
            (proc_number, last_action),
            Duration(micros=0)
        )
        self._proc_and_action_to_sum_duration[proc_number, last_action] = \
            last_action_sum_duration + last_action_duration

    def _account_last_actions(self):
        for processor_number, (action, duration) in self._proc_to_last_action_duration.items():
            action_sum_duration = self._proc_and_action_to_sum_duration.get(
                (processor_number, action),
                Duration(micros=0)
            )
            self._proc_and_action_to_sum_duration[processor_number, action] = \
                action_sum_duration + duration
        self._proc_to_last_action_duration.clear()

    def _generate_report(self) -> Report:
        processor_work_ratio = self._processors_work_ratio()

        return Report(
            log_name=self.name,
            simulation_duration=self._duration,
            avg_processor_task_handling=self._avg_time_per_action(_Action.PROCESSING),
            processor_task_handling_percentage=processor_work_ratio.get(_Action.PROCESSING, 0),
            avg_processor_waiting=self._avg_time_per_action(_Action.WAITING),
            processor_waiting_percentage=processor_work_ratio.get(_Action.WAITING, 0),
            avg_processor_overhead_work=self._avg_time_per_action(_Action.OVERHEAD),
            processor_overhead_work_percentage=processor_work_ratio.get(_Action.OVERHEAD, 0)
        )

    def _avg_time_per_action(self, action: _Action) -> Duration:
        return Duration.avg(
            *[
                self._proc_and_action_to_sum_duration.get((processor_num, action), Duration(micros=0))
                for processor_num
                in self._numbers_of_processors()
            ]
        )

    def _processors_work_ratio(self) -> Dict[_Action, Percentage]:
        numbers_of_processors = self._numbers_of_processors()
        processors_number = len(numbers_of_processors)

        processor_and_action_to_processing_percentage: Dict[Tuple[ProcessorNumber, _Action], Percentage] = {}
        for processor_number in numbers_of_processors:
            processor_action_to_sum_duration: Dict[_Action, Duration] = dict([
                (
                    action,
                    self._proc_and_action_to_sum_duration.get((processor_number, action), Duration.zero())
                )
                for action
                in _Action
            ])
            sum_duration_of_all_actions = Duration.sum(*processor_action_to_sum_duration.values())

            for action, sum_duration_of_action in processor_action_to_sum_duration.items():
                processor_and_action_to_processing_percentage[processor_number, action] = \
                    Percentage(float(sum_duration_of_action.micros) * 100 / sum_duration_of_all_actions.micros)

        action_to_percentage: Dict[_Action, Percentage] = {}
        for action in _Action:
            sum_of_action_percentage_of_processors = sum(
                [
                    processor_and_action_to_processing_percentage[proc_number, action]
                    for proc_number
                    in numbers_of_processors
                ]
            )
            action_to_percentage[action] = \
                Percentage(sum_of_action_percentage_of_processors / processors_number) \
                    if processors_number != 0 \
                    else Percentage(0)

        return action_to_percentage

    def _numbers_of_processors(self) -> Set[ProcessorNumber]:
        return set([proc_num for proc_num, action in self._proc_and_action_to_sum_duration.keys()])

    @staticmethod
    def _avg_percentage(percentages: Union[Collection[Percentage], ValuesView[Percentage]]) -> Percentage:
        sum_of_all = 0
        for percentage in percentages:
            sum_of_all += percentage
        return Percentage(sum_of_all / len(percentages))


_available_colours: List[str] = ["red", "green", "yellow", "blue", "magenta", "cyan", "white"]
shuffle(_available_colours)
_last_color_position: List[int] = [0]
_assigned_colours: Dict[str, str] = {}


def print_coloured(report: Report):
    colour = _assigned_colours.get(report.log_name)
    if colour is None:
        _color_position = _last_color_position[0] % len(_available_colours)
        _last_color_position[0] = _color_position + 1
        colour = _available_colours[_color_position]
        _assigned_colours[report.log_name] = colour

    print(colored(str(report), color=colour))
