from powerbase.conditions import (
    TaskStarted, 

    TaskFinished, 
    TaskFailed, 
    TaskSucceeded,

    TaskExecutable,

    DependFinish,
    DependFailure,
    DependSuccess
)
from powerbase.time import (
    TimeDelta, 
    TimeOfDay
)

from powerbase.core.task import Task
from powerbase.core.conditions import set_statement_defaults
from powerbase.core import Scheduler
from powerbase.task import FuncTask

import pytest
import pandas as pd
from dateutil.tz import tzlocal

import logging
import time
import datetime

Task.use_instance_naming = True

def run_task(fail=False):
    print("Running func")
    if fail:
        raise RuntimeError("Task failed")

@pytest.mark.parametrize('execution_number', range(10))
def test_task_status_race(tmpdir, session, execution_number):

    # c = logging.LogRecord("",1, "a", "a", "2", (), "").created
    # c = time.time()
    # t = time.time()
    # c = datetime.datetime.fromtimestamp(c)
    # t = datetime.datetime.now()
    # assert t >= c
    # return

    condition = TaskFinished(task="runned task")
    task = FuncTask(
        run_task, 
        name="runned task",
        execution="main"
    )
    task(params={"fail": False})

    # Imitating the __bool__
    assert condition.observe(task=task)
    return

    t = time.time()
    now = condition.observe()
    interv = task.period.rollback(now)
    _start_, _end_ = interv.left, interv.right

    records = task.logger.get_records(timestamp=(_start_, _end_), action=["success", "fail", "terminate"])
    records = [record["timestamp"] for record in records]
    try:
        assert bool(records)
    except:
        timestamp = [r['timestamp'] for r in list(task.logger.get_records())][-1]
        print(f"Now: {now}\nStart: {_start_}\nEnd: {_end_}\nAll records: {timestamp}")
        raise

@pytest.mark.parametrize(
    "cls,succeeding,expected",
    [
        pytest.param(
            TaskFinished, True, 
            True,
            id="TaskFinished Success"),
        pytest.param(
            TaskFinished, False, 
            True,
            id="TaskFinished Failure"),

        pytest.param(
            TaskSucceeded, True, 
            True,
            id="TaskSucceeded Success"),
        pytest.param(
            TaskSucceeded, False, 
            False,
            id="TaskSucceeded Failure"),

        pytest.param(
            TaskFailed, True, 
            False,
            id="TaskFailed Success"),
        pytest.param(
            TaskFailed, False, 
            True,
            id="TaskFailed Failure"),
    ],
)
def test_task_status(tmpdir, session, cls, succeeding, expected):
    # RACE CONDITION 2021-08-16: 'TaskFailed Failure' failed due to assert bool(condition) if expected else not bool(condition)

    with tmpdir.as_cwd() as old_dir:
        condition = cls(task="runned task")

        task = FuncTask(
            run_task, 
            name="runned task",
            execution="main"
        )

        # Has not yet ran
        assert not bool(condition)

        # Now has
        try:
            task(params={"fail": not succeeding})
        except: 
            pass

        # we sleep 20ms to 
        # There is a very small inaccuracy in time.time() that is used by
        # logging library to create LogRecord.created. On Windows this 
        # inaccuracy can be 16ms (https://stackoverflow.com/questions/1938048/high-precision-clock-in-python)
        # and in some cases the task is not registered to have run as 
        # in memory logging is way too fast. Therefore we just wait
        # 20ms to fix the issue
        # time.sleep(0.02) 
        assert bool(condition) if expected else not bool(condition)


@pytest.mark.parametrize(
    "cls,expected",
    [
        pytest.param(
            DependFinish, 
            True,
            id="DependFinish"),

        pytest.param(
            DependSuccess, 
            False,
            id="DependSuccess"),

        pytest.param(
            DependFailure, 
            True,
            id="DependFailure"),
    ],
)
def test_task_depend_fail(tmpdir, session, cls, expected):
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:
        condition = cls(task="runned task", depend_task="prerequisite task")

        depend_task = FuncTask(
            run_task, 
            name="prerequisite task",
            execution="main"
        )

        task = FuncTask(
            run_task, 
            name="runned task",
            execution="main"
        )

        # ------------------------ t0
        assert not bool(condition)


        # depend_task
        # -----|------------------- t0
        try: depend_task(params={"fail": True})
        except: pass
        assert bool(condition) if expected else not bool(condition)


        # depend_task     task
        # -----|-----------|------- t0
        task()
        assert not bool(condition)


        # depend_task     task     depend_task
        # -----|-----------|-----------|----------- t0
        try: depend_task(params={"fail": True})
        except: pass
        assert bool(condition) if expected else not bool(condition)


        # depend_task     task     depend_task     task
        # -----|-----------|-----------|------------|-------- t0
        task()
        assert not bool(condition)


@pytest.mark.parametrize(
    "cls,expected",
    [
        pytest.param(
            DependFinish, 
            True,
            id="DependFinish"),

        pytest.param(
            DependSuccess, 
            True,
            id="DependSuccess"),

        pytest.param(
            DependFailure, 
            False,
            id="DependFailure"),
    ],
)
def test_task_depend_success(tmpdir, session, cls, expected):
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:
        condition = cls(task="runned task", depend_task="prerequisite task")

        depend_task = FuncTask(
            run_task, 
            name="prerequisite task",
            execution="main"
        )

        task = FuncTask(
            run_task, 
            name="runned task",
            execution="main"
        )

        # ------------------------ t0
        assert not bool(condition)


        # depend_task
        # -----|------------------- t0
        depend_task(params={"fail": False})
        assert bool(condition) if expected else not bool(condition)


        # depend_task     task
        # -----|-----------|------- t0
        task()
        assert not bool(condition)


        # depend_task     task     depend_task
        # -----|-----------|-----------|----------- t0
        depend_task(params={"fail": False})
        assert bool(condition) if expected else not bool(condition)


        # depend_task     task     depend_task     task
        # -----|-----------|-----------|------------|-------- t0
        task()
        assert not bool(condition)

