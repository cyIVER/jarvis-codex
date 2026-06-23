from __future__ import annotations

import os
import pty
import queue
import shlex
import signal
import struct
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .policy import PolicyDecision, PolicyProfile, classify_command


@dataclass(frozen=True)
class PtyOutputChunk:
    channel_id: str
    stream_type: Literal["stdout"]
    chunk: str
    sequence: int

    def to_dict(self) -> dict[str, object]:
        return {
            "channel_id": self.channel_id,
            "stream_type": self.stream_type,
            "chunk": self.chunk,
            "sequence": self.sequence,
        }


@dataclass(frozen=True)
class PtySpawnResult:
    channel_id: str
    pid: int
    command: str
    profile: PolicyProfile
    policy: PolicyDecision

    def to_dict(self) -> dict[str, object]:
        return {
            "channel_id": self.channel_id,
            "pid": self.pid,
            "command": self.command,
            "profile": self.profile,
            "policy": self.policy.to_dict(),
        }


class PtyPolicyError(PermissionError):
    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


class PtyNotFoundError(KeyError):
    pass


class ManagedPty:
    def __init__(
        self,
        *,
        channel_id: str,
        command: str,
        profile: PolicyProfile,
        process: subprocess.Popen[bytes],
        master_fd: int,
    ) -> None:
        self.channel_id = channel_id
        self.command = command
        self.profile = profile
        self.process = process
        self.master_fd = master_fd
        self.created_at = time.time()
        self._sequence = 0
        self._closed = False
        self._output: queue.Queue[PtyOutputChunk] = queue.Queue()
        self._reader = threading.Thread(target=self._read_loop, name=f"pty-reader-{channel_id}", daemon=True)
        self._reader.start()

    @property
    def pid(self) -> int:
        return int(self.process.pid)

    @property
    def returncode(self) -> int | None:
        return self.process.poll()

    def write(self, text: str) -> None:
        os.write(self.master_fd, text.encode("utf-8", errors="replace"))

    def resize(self, *, rows: int, cols: int) -> None:
        if rows <= 0 or cols <= 0:
            raise ValueError("rows and cols must be positive")
        import fcntl
        import termios

        packed = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, packed)

    def kill(self, *, sig: int = signal.SIGTERM) -> int | None:
        try:
            if self.process.poll() is None:
                try:
                    os.killpg(self.process.pid, sig)
                except ProcessLookupError:
                    pass
            try:
                return self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                return self.process.wait(timeout=2)
        finally:
            self.close_master()

    def wait(self, timeout: float | None = None) -> int:
        return self.process.wait(timeout=timeout)

    def drain_output(self) -> list[PtyOutputChunk]:
        chunks: list[PtyOutputChunk] = []
        while True:
            try:
                chunks.append(self._output.get_nowait())
            except queue.Empty:
                return chunks

    def close(self) -> None:
        try:
            self.kill()
        finally:
            self.close_master()

    def close_master(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            os.close(self.master_fd)
        except OSError:
            pass

    def _read_loop(self) -> None:
        try:
            while True:
                try:
                    data = os.read(self.master_fd, 4096)
                except OSError:
                    return
                if not data:
                    return
                self._sequence += 1
                self._output.put(
                    PtyOutputChunk(
                        channel_id=self.channel_id,
                        stream_type="stdout",
                        chunk=data.decode("utf-8", errors="replace"),
                        sequence=self._sequence,
                    )
                )
        finally:
            self.process.poll()


class PtySupervisor:
    def __init__(self) -> None:
        self._channels: dict[str, ManagedPty] = {}
        self._lock = threading.Lock()

    def spawn(
        self,
        command: str,
        *,
        profile: PolicyProfile = "observe",
        cwd: Path | str | None = None,
    ) -> PtySpawnResult:
        decision = classify_command(command, profile)
        if not decision.allowed:
            raise PtyPolicyError(decision)

        argv = shlex.split(decision.command)
        if not argv:
            raise ValueError("command is empty")

        channel_id = self._new_channel_id()
        master_fd, slave_fd = pty.openpty()
        try:
            process = subprocess.Popen(
                argv,
                cwd=str(cwd) if cwd is not None else None,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                start_new_session=True,
                close_fds=True,
            )
        except Exception:
            os.close(slave_fd)
            os.close(master_fd)
            raise
        finally:
            try:
                os.close(slave_fd)
            except OSError:
                pass

        try:
            managed = ManagedPty(
                channel_id=channel_id,
                command=decision.command,
                profile=profile,
                process=process,
                master_fd=master_fd,
            )
            with self._lock:
                self._channels[channel_id] = managed
        except Exception:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=2)
            except Exception:
                pass
            try:
                os.close(master_fd)
            except OSError:
                pass
            raise
        return PtySpawnResult(
            channel_id=channel_id,
            pid=process.pid,
            command=decision.command,
            profile=profile,
            policy=decision,
        )

    def get(self, channel_id: str) -> ManagedPty:
        with self._lock:
            try:
                return self._channels[channel_id]
            except KeyError as exc:
                raise PtyNotFoundError(channel_id) from exc

    def write(self, channel_id: str, text: str) -> None:
        self.get(channel_id).write(text)

    def resize(self, channel_id: str, *, rows: int, cols: int) -> None:
        self.get(channel_id).resize(rows=rows, cols=cols)

    def kill(self, channel_id: str) -> int | None:
        return self.get(channel_id).kill()

    def drain_output(self, channel_id: str) -> list[PtyOutputChunk]:
        return self.get(channel_id).drain_output()

    def cleanup_finished(self) -> list[str]:
        removed: list[str] = []
        with self._lock:
            for channel_id, managed in list(self._channels.items()):
                if managed.returncode is not None:
                    removed.append(channel_id)
                    self._channels.pop(channel_id, None)
                    managed.close_master()
        return removed

    def close_all(self) -> None:
        with self._lock:
            channels = list(self._channels.values())
            self._channels.clear()
        for managed in channels:
            managed.close()

    def _new_channel_id(self) -> str:
        with self._lock:
            while True:
                channel_id = f"pty_{uuid.uuid4().hex[:16]}"
                if channel_id not in self._channels:
                    return channel_id
