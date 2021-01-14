from src.sys.time.duration import Duration


def thread_context_switch_overhead() -> Duration:
    # Context Switch Overheads for Linux on ARM Platforms (p.5)
    a = Duration(micros=48)

    # Analysis of Optimal Thread Pool Size (p.46)
    b = Duration(micros=20)

    return Duration.avg(a, b)


def thread_creation_cost() -> Duration:
    # Comparative performance evaluation of Java threads for embedded applications:
    # Linux Thread vs. Green Thread (p. 223)
    a = Duration(micros=8)

    # Analysis of Optimal Thread Pool Size (p. 46)
    b = Duration(micros=422)
    return Duration.avg(a, b)


def thread_destruction_cost() -> Duration:
    # Comparative performance evaluation of Java threads for embedded applications:
    # Linux Thread vs. Green Thread (p. 223)
    return Duration(micros=1)


def thread_timeslice() -> Duration:
    return Duration(millis=100)  # https://github.com/torvalds/linux/blob/master/include/linux/sched/rt.h RR_TIMESLICE
