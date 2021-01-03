from unittest import TestCase

from bin.sys.time.time import TimeDelta
from bin.sys.time.duration import Duration


class TestTimeDelta(TestCase):
    def test_new_instance_should_be_unique(self):
        # given
        first = TimeDelta(duration=Duration(micros=1))
        second = TimeDelta(duration=Duration(micros=1))

        # when
        equals = first.__eq__(second)

        # then
        self.assertFalse(equals)

    def test_new_instance_should_have_unique_identifier(self):
        # given
        first = TimeDelta(duration=Duration(micros=1))
        second = TimeDelta(duration=Duration(micros=1))

        # when
        first_id = first.identifier
        second_id = second.identifier

        # then
        self.assertNotEqual(first_id, second_id)
