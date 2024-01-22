import threading
import graphviz
import sys
import os
import subprocess
import multiprocessing as mp
import typing
from typing import Any
import signal

import cvde
from cvde.job import JobSubmission

T = typing.TypeVar("T")


class DAG(typing.Generic[T]):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._edges: dict[T, list[T]] = {}
        self._nodes: list[T] = []

    def add_node(self, node: T, to_nodes: list[T] = []) -> None:
        with self._lock:
            self._nodes.append(node)
            self._edges[node] = to_nodes

    def add_edge(self, from_node: T, to_node: T) -> None:
        if from_node == to_node:
            return

        with self._lock:
            self._edges[from_node].append(to_node)

    def add_edges(self, from_node: T, to_nodes: list[T]) -> None:
        with self._lock:
            self._edges[from_node].extend([n for n in to_nodes if n != from_node])

    def get_digraph(
        self, format: typing.Callable[[T], str] = lambda x: str(x), node_colors: dict[T, str] = {}
    ) -> graphviz.Digraph:
        graph = graphviz.Digraph()

        graph.attr("graph", rankdir="LR", bgcolor="transparent", splines="ortho")

        with self._lock:
            for node in self._nodes:
                graph.node(
                    format(node),
                    shape="box",
                    color=node_colors.get(node, "white"),
                    fontcolor="white",
                )

            for from_node, to_nodes in self._edges.items():
                for to_node in to_nodes:
                    # flipped for indicating execution order
                    graph.edge(format(to_node), format(from_node), color="white")
        return graph

    def pop(self, node: T) -> None:
        with self._lock:
            self._nodes.remove(node)
            self._edges.pop(node)
            for edges in self._edges.values():
                if node in edges:
                    edges.remove(node)

    def get_all_nodes(self) -> list[T]:
        with self._lock:
            return self._nodes.copy()

    def get_leaves(self) -> list[T]:
        with self._lock:
            leaves = [node for node, edges in self._edges.items() if len(edges) == 0]
        return leaves


class Scheduler:
    """schedule jobs"""

    def __init__(self) -> None:
        self._current: dict[mp.Process, JobSubmission] = {}
        self._lock_current = threading.Lock()
        self._executiongraph: DAG[JobSubmission] = DAG()

    @property
    def current(self) -> dict[mp.Process, JobSubmission]:
        with self._lock_current:
            return self._current

    def submit(self, sub: JobSubmission, wait_for: list[JobSubmission] = []) -> None:
        self._executiongraph.add_node(sub, wait_for)
        self.launch_ready_submissions()

    def cancel(self, sub: JobSubmission) -> None:
        """Cancel a job submission before it launches."""
        assert sub not in self._current.values(), "Can not cancel running job."
        self._executiongraph.pop(sub)

    def get_scheduled_submissions(self) -> list[JobSubmission]:
        return self._executiongraph.get_all_nodes()

    def get_digraph(self) -> graphviz.Digraph:
        colors = {submission: "red" for submission in self.current.values()}
        return self._executiongraph.get_digraph(
            format=lambda x: f"{x.run_name} ({x.job_name})", node_colors=colors
        )

    def watchdog(self, process: mp.Process) -> None:
        process.join()
        submission = self.current.pop(process)
        self._executiongraph.pop(submission)
        self.launch_ready_submissions()
        cvde.gui.update_gui_from_thread()

    def launch_ready_submissions(self) -> None:
        def not_yet_launched(submission: JobSubmission) -> bool:
            return submission not in self.current.values()

        ready_submissions = filter(not_yet_launched, self._executiongraph.get_leaves())
        for submission in ready_submissions:
            print(f"Launched {submission.run_name}")
            process = mp.Process(
                target=_run,
                args=(submission,),
                daemon=True,
            )

            process.start()
            self.current[process] = submission
            threading.Thread(target=self.watchdog, args=(process,), daemon=True).start()


def _run(submission: JobSubmission) -> None:
    """in new Process"""
    for k, v in submission.env.items():
        os.environ[k] = v

    logger = cvde.job.RunLogger.create(submission)

    if cvde.Workspace().git_tracking_enabled:
        subprocess.run(
            ["git", "clone", ".", logger.workspace.resolve()], capture_output=True
        ).check_returncode()

        os.chdir(logger.workspace)
        assert submission.commit is not None
        assert submission.diff is not None

        print("Checkout out to last commit at submission time.")
        print(submission.commit)
        subprocess.run(
            ["git", "checkout", submission.commit], capture_output=True
        ).check_returncode()
        print("Applying uncommitted changes at submission time.")

        subprocess.run(
            ["git", "apply", logger.root.joinpath("uncommitted.diff").resolve()],
            capture_output=True,
        ).check_returncode()

    job_fn = cvde.Workspace().list_jobs()[submission.job_name]
    job = job_fn(logger=logger, config=submission.config)

    def handler(sig: int, frame: Any) -> None:
        print("Terminated by user.")
        job.on_terminate()
        exit(0)

    signal.signal(signal.SIGTERM, handler)

    assert isinstance(sys.stdout, cvde.ThreadPrinter)
    assert isinstance(sys.stderr, cvde.ThreadPrinter)

    # print stdout, err to files as well
    sys.stdout.register_new_out(job.tracker.stdout_file)
    sys.stderr.register_new_out(job.tracker.stderr_file)

    # job.run()
    import time

    for _ in range(10):
        time.sleep(1)
        print("alive")
    print("done")


# def on_launch() -> None:
#     # clone repo into /tmp/<run_name>
#     os.system("git clone . /tmp/<run_name>")

#     # IN THE TEMPORAY DIRECTORY
#     # checkout commit hash
#     os.system("git checkout $(cat commit_hash.txt)")
#     # apply diff
#     os.system("git apply output_file.txt")
