.. _advanced-tutorial:

Advanced Tutorial
=================

This is an advanced level tutorial.

Task References
---------------

Each task should have a unique name within
the session. So far we have not set the name
ourselves and let Rocketry to come up with
such (from the functions we used as tasks).

You can pass the name yourself:

.. literalinclude:: /code/naming.py
    :language: py

If you don't give a name for the task, the 
task itself will make up a name for it. For
function tasks, the name of the task is the 
name of the function (combined with import path).

Function tasks created by decorating functions 
(the method we have done so far) can also be 
addressed using the function instance. There 
is a special attribute stored in the function
that contains the real name of the task so 
the session can look it up if you ask the task 
from the session.


Task Types
----------

So far, we have only used ``FuncTask`` with passing a callable.
There are other task types as well to cover most common use cases:

- ``FuncTask``: Executes a Python function
- ``CommandTask``: Executes a shell command
- ``CodeTask``: Executes raw code as string. Potentially dangerous.

Here are the ways to initialize tasks:

.. code-block:: python

    @app.task('daily')
    def do_things():
        ...

    def run_things():
        ...
    
    app.task('daily', func=run_things)

    app.task('daily', func_name="main", path="path/to/example.py")

    app.task('daily', command='echo "Hello world"')

    app.task('daily', code='print("Hello world")')


Metatasks
---------

The scheduler system can be modified in runtime.
You could during the runtime:

- shut down the scheduler
- restart the scheduler
- force a task to be run
- disable a task
- create, update or delete tasks

To do there, you can create a task that
runs either as a separate thread or on 
the main loop and pass the session or a
task in the task parameters. Tasks parallelized as 
separate processes cannot alter the 
scheduling environment due to limitations 
with sharing memory. 

To access the session:

.. code-block:: python

    from rocketry.args import Session

    @app.task(execution="thread")
    def do_shutdown(session=Session()):
        session.shutdown()

You can also access other tasks in runtime.
To do so, use ``Session`` or ``Task`` 
arguments to access tasks. 

We have the following task:

.. code-block:: python

    @app.task()
    def do_things():
        ... # Just some task

To access this task using the ``Session`` argument:

.. code-block:: python

    from rocketry.args import Session

    @app.task(execution="thread")
    def read_task(session=Session()):
        # Get by name
        task = session['do_things']

        # Or by function
        task = session[do_things]
        ...

        # Or just loop the tasks
        for task in session.tasks:
            if task.name == "do_things":
                break
        ...

To access this task using the ``Task`` argument:

.. code-block:: python

    from rocketry.args import Task

    @app.task(execution="thread")
    def read_task(task=Task(do_things)):
        ...

Access Task Logs
----------------

Now that we know how to access tasks in runtime,
we can read the logs of our task.

Let's take this again as an example:

.. code-block:: python

    @app.task()
    def do_things():
        ...

Then we make a task that fetch the task and queries
its log:

.. code-block:: python

    from rocketry.args import Session

    @app.task(execution="thread")
    def read_logs(session=Session()):
        task = session['do_things']

        run_logs = task.logger.filter_by(action="run").all()
        success_logs = task.logger.filter_by(action="success").all()
        fail_logs = task.logger.filter_by(action="fail").all()
        ...
