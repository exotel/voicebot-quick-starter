"""Default runner — launches the common bot over Pipecat WebRTC transport.

Run:  python default_runner.py
Then open http://localhost:7860/client in your browser and click Connect.
"""

from bot import run_bot

from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.transports.base_transport import TransportParams


async def bot(runner_args: RunnerArguments):
    """Entry point for Pipecat runner (WebRTC mode)."""
    transport_params = {
        "webrtc": lambda: TransportParams(audio_in_enabled=True, audio_out_enabled=True),
    }
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
