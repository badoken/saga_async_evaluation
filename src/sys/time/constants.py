from src.sys.time.duration import Duration


def threads_context_switch_overhead() -> Duration:
    return Duration(micros=48)  # Context Switch Overheads for Linux on ARM Platforms (p.5)


def thread_timeslice() -> Duration:
    return Duration(millis=100)  # https://github.com/torvalds/linux/blob/master/include/linux/sched/rt.h RR_TIMESLICE
