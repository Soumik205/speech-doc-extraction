import asyncio
import re
import tempfile

from app.services.domain import AudioProbeResult

_MEAN_VOLUME_RE = re.compile(r"mean_volume:\s*(-inf|-?\d+(?:\.\d+)?)\s*dB")


async def _run(cmd: list[str]) -> tuple[int, bytes, bytes]:
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout, stderr


async def probe_audio(audio_bytes: bytes, silence_threshold_dbfs: float) -> AudioProbeResult:
    with tempfile.NamedTemporaryFile(suffix=".audio") as tmp:
        tmp.write(audio_bytes)
        tmp.flush()

        try:
            returncode, stdout, _ = await _run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    tmp.name,
                ]
            )
        except FileNotFoundError as exc:
            return AudioProbeResult(None, None, error=f"ffprobe is not available: {exc}")

        if returncode != 0:
            return AudioProbeResult(None, None, error="ffprobe could not read the file; it may be undecodable")

        try:
            duration_seconds = float(stdout.decode().strip())
        except ValueError:
            return AudioProbeResult(None, None, error="ffprobe did not return a usable duration")

        try:
            returncode, _, stderr = await _run(
                ["ffmpeg", "-i", tmp.name, "-af", "volumedetect", "-f", "null", "-"]
            )
        except FileNotFoundError as exc:
            return AudioProbeResult(None, None, error=f"ffmpeg is not available: {exc}")

        match = _MEAN_VOLUME_RE.search(stderr.decode(errors="replace"))
        if returncode != 0 or match is None:
            return AudioProbeResult(
                None, None, error="ffmpeg could not determine audio volume; file may be undecodable"
            )

        mean_volume_dbfs = float("-inf") if match.group(1) == "-inf" else float(match.group(1))
        is_silent = mean_volume_dbfs <= silence_threshold_dbfs

    return AudioProbeResult(duration_seconds=duration_seconds, is_silent=is_silent, error=None)
