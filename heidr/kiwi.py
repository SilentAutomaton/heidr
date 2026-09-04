"""Talking to a public KiwiSDR receiver directly.

The receiver speaks one WebSocket that carries both the tuning commands and the
audio. There is no HTTP endpoint for the sound — the firmware's whole routing
table is four sockets and a handful of status queries — so a client is the only
way in.

The client is here rather than borrowed. `kiwiclient`, the one everybody uses,
carries no licence file at all, which makes it all rights reserved: it cannot be
vendored, packaged or depended on. A wire protocol is not a work of authorship,
so this is written from what the receiver actually sends.

Asking for `compression=0` is what keeps it short. The receiver then sends plain
big-endian 16-bit samples instead of IMA ADPCM, and the decoder — the one part
that would have been tempting to copy — is not needed at all.
"""

import base64
import os
import socket
import struct
import time
from typing import Iterator

import numpy as np

PORT = 8073
# What the receiver sends, whatever is asked for. The recogniser wants 16 kHz.
NATIVE_RATE = 12000
AUDIO = b"SND"
# b"SND", a flags byte, a sequence number, and an S-meter reading.
HEADER = 10
CONNECT_S = 8.0
REDIRECTS = 3
PASSBAND = (-4000, 4000)


class Link:
    """One WebSocket, read frame by frame.

    Small enough to keep: the receiver never masks what it sends, never
    fragments an audio frame, and never asks anything of the client.
    """

    def __init__(self, sock: socket.socket, rest: bytes = b""):
        self.sock = sock
        self.rest = rest

    def send(self, text: str) -> None:
        payload = text.encode()
        mask = os.urandom(4)
        header = bytearray([0x81])
        size = len(payload)
        if size < 126:
            header.append(0x80 | size)
        elif size < 1 << 16:
            header.append(0x80 | 126)
            header += struct.pack(">H", size)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", size)
        header += mask
        self.sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def take(self, size: int) -> bytes:
        while len(self.rest) < size:
            chunk = self.sock.recv(max(size - len(self.rest), 4096))
            if not chunk:
                raise ConnectionError("the receiver closed the connection")
            self.rest += chunk
        taken, self.rest = self.rest[:size], self.rest[size:]
        return taken

    def frame(self) -> bytes:
        _first, second = self.take(2)
        size = second & 0x7F
        if size == 126:
            size = struct.unpack(">H", self.take(2))[0]
        elif size == 127:
            size = struct.unpack(">Q", self.take(8))[0]
        return self.take(size) if size else b""

    def close(self) -> None:
        self.sock.close()


def address(url: str) -> tuple[str, int]:
    """Host and port out of a directory entry.

    A third of the public list is behind `proxy.kiwisdr.com`, which answers port
    80 with a redirect to 8073. Going straight there saves the round trip.
    """
    bare = url.split("//")[-1].rstrip("/")
    host, _, port = bare.partition(":")
    return host, int(port) if port.isdigit() else PORT


def open_link(host: str, port: int, timeout: float = CONNECT_S) -> Link:
    """The socket, following the proxy service's redirects to get to it.

    A third of the public list sits behind `proxy.kiwisdr.com`, which answers
    with a redirect, and sometimes with a second one to a different proxy. Three
    hops is more than any of them use and stops a loop from being endless.
    """
    path = f"/kiwi/{int(time.time())}/SND"
    for _hop in range(REDIRECTS):
        sock, head, rest = _shake(host, port, path, timeout)
        status = head.split(b"\r\n")[0]
        if b" 101 " in status:
            # The first audio frame can arrive in the same packet as the reply.
            return Link(sock, rest)
        sock.close()
        location = _header(head, b"location")
        if not location:
            raise ConnectionError(status.decode(errors="replace"))
        host, port, path = _split(location)
    raise ConnectionError(f"{host} redirected more than {REDIRECTS} times")


def _shake(host: str, port: int, path: str, timeout: float):
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.settimeout(timeout)
    key = base64.b64encode(os.urandom(16)).decode()
    # The timestamp in the path is only a cache-buster. An open receiver wants
    # no token and sets no cookie.
    sock.sendall(
        (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode()
    )
    reply = b""
    while b"\r\n\r\n" not in reply:
        chunk = sock.recv(4096)
        if not chunk:
            sock.close()
            raise ConnectionError("the receiver closed the connection during the handshake")
        reply += chunk
    head, _, rest = reply.partition(b"\r\n\r\n")
    return sock, head, rest


def _header(head: bytes, wanted: bytes) -> str:
    for line in head.split(b"\r\n")[1:]:
        name, _, value = line.partition(b":")
        if name.strip().lower() == wanted:
            return value.strip().decode(errors="replace")
    return ""


def _split(location: str) -> tuple[str, int, str]:
    bare = location.split("//")[-1]
    authority, _, path = bare.partition("/")
    host, port = address(authority)
    return host, port, "/" + path


def tune(link: Link, kilohertz: float, mode: str, agent: str) -> None:
    """Put the receiver on a frequency and ask for uncompressed audio.

    The order matters and is not documented anywhere: the rate has to wait for
    the receiver to announce itself. Sent earlier, it is accepted and then no
    audio frame ever arrives.
    """
    link.send("SET auth t=kiwi p=")
    while b"audio_rate=" not in link.frame():
        pass

    link.send(f"SET AR OK in={NATIVE_RATE} out=44100")
    link.send(f"SET ident_user={agent}")
    link.send(f"SET mod={mode} low_cut={PASSBAND[0]} high_cut={PASSBAND[1]} freq={kilohertz:.2f}")
    link.send("SET compression=0")
    link.send("SET agc=1 hang=0 thresh=-100 slope=6 decay=1000 manGain=50")


def capture(host: str, port: int, kilohertz: float, mode: str, rate: int, seconds: float,
            agent: str) -> Iterator[np.ndarray]:
    deadline = time.monotonic() + seconds + CONNECT_S
    try:
        link = open_link(host, port, CONNECT_S)
    except (OSError, ConnectionError):
        return
    wanted = int(seconds * rate)
    heard = 0
    try:
        tune(link, kilohertz, mode, agent)
        # Two bounds, and both are needed. The count is what was asked for; the
        # deadline is what a receiver that goes quiet gets instead.
        while heard < wanted and time.monotonic() < deadline:
            payload = link.frame()
            if payload[:3] != AUDIO or len(payload) <= HEADER:
                continue
            block = resample(samples(payload[HEADER:]), rate)
            heard += block.size
            yield block
    except (OSError, ConnectionError):
        # A receiver that stops answering is an ordinary thing to find. What was
        # heard before it stopped is kept, and the caller moves to the next one.
        return
    finally:
        link.close()


def samples(raw: bytes) -> np.ndarray:
    """Big-endian, unlike everything else here. That is what the receiver sends."""
    whole = len(raw) - len(raw) % 2
    return np.frombuffer(raw[:whole], dtype=">i2").astype(np.float32) / 32768.0


def resample(block: np.ndarray, rate: int) -> np.ndarray:
    """Straight lines between the samples, which is enough for speech.

    Done per block, so the joins are not interpolated across. At five hundred
    samples a block the seam is one sample wide and well under what a recogniser
    can hear.
    """
    if rate == NATIVE_RATE or block.size == 0:
        return block
    count = max(1, int(block.size * rate / NATIVE_RATE))
    wanted = np.linspace(0, block.size, count, endpoint=False)
    return np.interp(wanted, np.arange(block.size), block).astype(np.float32)
