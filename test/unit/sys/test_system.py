from typing import List
from unittest import TestCase
from unittest.mock import Mock, call

from src.sys.processor import Processor, ProcessorFactory
from src.sys.system import System, ProcessingMode
from src.sys.time.duration import Duration
from src.sys.time.time import TimeDelta
from src.sys.thread import KernelThread, ChainOfExecutables
from test.unit.sys.factories import create_executables


class TestSystem(TestCase):
    def test_should_publish_all_tasks_to_proc_if_in_overloaded_mode(self):
        # given
        factory = proc_factory(yielding_is_on=False)
        processor1 = proc_mock(factory)
        processor2 = proc_mock(factory)

        system = System(
            processors_count=2,
            processing_mode=ProcessingMode.OVERLOADED_PROCESSORS,
            proc_factory=factory
        )

        executable1, executable2, executable3, executable4 = create_executables(4)

        delta1 = TimeDelta(Duration(micros=1))
        delta2 = TimeDelta(Duration(micros=1))

        # when
        system.publish([executable1, executable2, executable3, executable4])
        system.tick(time_delta=delta1)
        system.tick(time_delta=delta2)

        # then
        processor1.assign.assert_has_calls([call(KernelThread(executable1)), call(KernelThread(executable3))])
        processor1Thread1, processor1Thread2 = retrieve_assigned_threads(processor1)
        self.assertIsNot(processor1Thread1, processor1Thread2)
        processor1.ticked.assert_has_calls([call(time_delta=delta1), call(time_delta=delta2)])

        processor2.assign.assert_has_calls([call(KernelThread(executable2)), call(KernelThread(executable4))])
        processor2Thread1, processor2Thread2 = retrieve_assigned_threads(processor2)
        self.assertIsNot(processor2Thread1, processor2Thread2)
        processor2.ticked.assert_has_calls([call(time_delta=delta1), call(time_delta=delta2)])

    def test_should_publish_all_tasks_to_proc_if_in_yielding_mode(self):
        # given
        factory = proc_factory(yielding_is_on=True)
        processor1 = proc_mock(factory)
        processor2 = proc_mock(factory)

        system = System(
            processors_count=2,
            processing_mode=ProcessingMode.YIELDING_PROCESSORS,
            proc_factory=factory
        )

        executable1, executable2, executable3, executable4 = create_executables(4)

        delta1 = TimeDelta(Duration(micros=1))
        delta2 = TimeDelta(Duration(micros=1))

        # when
        system.publish([executable1, executable2, executable3, executable4])
        system.tick(time_delta=delta1)
        system.tick(time_delta=delta2)

        # then
        processor1.assign.assert_has_calls([call(KernelThread(executable1)), call(KernelThread(executable3))])
        processor1Thread1, processor1Thread2 = retrieve_assigned_threads(processor1)
        self.assertIsNot(processor1Thread1, processor1Thread2)
        processor1.ticked.assert_has_calls([call(time_delta=delta1), call(time_delta=delta2)])

        processor2.assign.assert_has_calls([call(KernelThread(executable2)), call(KernelThread(executable4))])
        processor2Thread1, processor2Thread2 = retrieve_assigned_threads(processor2)
        self.assertIsNot(processor2Thread1, processor2Thread2)
        processor2.ticked.assert_has_calls([call(time_delta=delta1), call(time_delta=delta2)])

    def test_should_publish_a_few_tasks_to_proc_in_cain_if_in_fixed_pool_mode(self):
        # given
        factory = proc_factory(yielding_is_on=False)
        processor1 = proc_mock(factory)
        processor2 = proc_mock(factory)

        system = System(processors_count=2, processing_mode=ProcessingMode.FIXED_POOL_SIZE, proc_factory=factory)

        executable1, executable2, executable3 = create_executables(3)

        # when
        delta1 = TimeDelta(Duration(micros=1))
        system.publish([executable1, executable2, executable3])
        system.tick(time_delta=delta1)

        # then
        processor1.assign.assert_called_once_with(KernelThread(ChainOfExecutables(executable1, executable3)))
        processor1.ticked.assert_called_once_with(time_delta=delta1)
        processor1Thread = retrieve_assigned_threads(processor1)[0]
        reset_proc_mock(processor1)

        processor2.assign.assert_called_once_with(KernelThread(ChainOfExecutables(executable2)))
        processor2.ticked.assert_called_once_with(time_delta=delta1)
        processor2Thread = retrieve_assigned_threads(processor2)[0]

        self.assertIsNot(processor1Thread, processor2Thread)

    def test_work_is_done_should_return_false_if_processors_are_not_starving(self):
        # given
        factory = proc_factory(yielding_is_on=False)
        processor1 = proc_mock(factory)
        processor1.is_starving = lambda: False
        system = System(processors_count=1, processing_mode=ProcessingMode.FIXED_POOL_SIZE,
                        proc_factory=factory)

        # when
        result = system.work_is_done()

        # then
        self.assertFalse(result)

    def test_work_is_done_should_return_true_if_there_are_no_tasks_in_the_pool_and_processors_are_starving(self):
        # given
        factory = proc_factory(yielding_is_on=False)
        processor1 = proc_mock(factory)
        processor1.is_starving = lambda: True
        system = System(processors_count=1, processing_mode=ProcessingMode.FIXED_POOL_SIZE,
                        proc_factory=factory)

        # when
        result = system.work_is_done()

        # then
        self.assertTrue(result)


def proc_factory(yielding_is_on: bool) -> ProcessorFactory:
    factory = ProcessorFactory()
    mocks = []
    factory.mocks = mocks
    factory.new = lambda count, processing_interval, yielding: \
        mocks \
            if count is len(mocks) and yielding == yielding_is_on \
            else None

    return factory


def proc_mock(factory: ProcessorFactory) -> Processor:
    processor1 = Processor(processing_interval=Duration(20), proc_number=1, yielding=False)
    processor1.ticked = Mock()
    processor1.assign = Mock(wraps=processor1.assign)
    factory.mocks.append(processor1)
    return processor1


def reset_proc_mock(processor: Processor):
    processor.assign.reset_mock()
    processor.ticked.reset_mock()


def retrieve_assigned_threads(processor_mock: Processor) -> List[KernelThread]:
    return processor_mock.assign.call_args
