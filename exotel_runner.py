"""Exotel runner — launches the common bot over Exotel telephony WebSocket.

Run:  python exotel_runner.py
"""

from loguru import logger

from bot import run_bot

from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import parse_telephony_websocket
from pipecat.serializers.exotel import ExotelFrameSerializer
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)


async def bot(runner_args: RunnerArguments):
    """Entry point for Pipecat runner (Exotel telephony mode)."""
    transport_type, call_data = await parse_telephony_websocket(runner_args.websocket)
    logger.info(f"Auto-detected transport: {transport_type}")

    serializer = ExotelFrameSerializer(
        stream_sid=call_data["stream_id"],
        call_sid=call_data["call_id"],
    )

    transport = FastAPIWebsocketTransport(
        websocket=runner_args.websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            serializer=serializer,
        ),
    )

    await run_bot(transport, runner_args, audio_sample_rate=8000)


if __name__ == "__main__":
    import sys

    # Auto-set transport to exotel unless the user explicitly overrides it
    if "-t" not in sys.argv and "--transport" not in sys.argv:
        sys.argv.extend(["-t", "exotel"])

    from pipecat.runner.run import main

    main()
