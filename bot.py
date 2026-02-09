"""Common bot logic: Google STT, Gemini Flash Lite (Vertex AI), Google TTS (Chirp3-HD).

This module exposes run_bot() which builds the full pipeline.
Use webrtc_runner.py or exotel_runner.py as entry points.
"""
import json
import os

from dotenv import load_dotenv
from loguru import logger

load_dotenv(override=True)

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.services.google.llm_vertex import GoogleVertexLLMService
from pipecat.services.google.stt import GoogleSTTService
from pipecat.services.google.tts import GoogleTTSService
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import BaseTransport


async def run_bot(
    transport: BaseTransport,
    runner_args: RunnerArguments,
    audio_sample_rate: int | None = None,
):
    """Build and run the voice-bot pipeline.

    Args:
        transport: The transport to use (WebRTC, Exotel WS, etc.).
        runner_args: Pipecat runner arguments.
        audio_sample_rate: Optional sample rate for audio in/out.
            Pass 8000 for telephony (Exotel). Leave None for defaults (WebRTC).
    """
    # Google Speech-to-Text
    stt = GoogleSTTService(
        params=GoogleSTTService.InputParams(languages=Language.EN_US, model="chirp_3"),
        credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        location="asia-south1",
    )
    # Google Gemini LLM via Vertex AI (Flash Lite)
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    with open(creds_path) as f:
        gcp_project = json.load(f)["project_id"]

    llm = GoogleVertexLLMService(
        credentials_path=creds_path,
        project_id=gcp_project,
        model="gemini-2.5-flash-lite",
        params=GoogleVertexLLMService.InputParams(
            temperature=0.7,
            max_tokens=200,
            thinking=GoogleVertexLLMService.ThinkingConfig(thinking_budget=0),
        ),
    )
    # Google Text-to-Speech (Chirp3-HD)
    tts = GoogleTTSService(
        voice_id="en-US-Chirp3-HD-Charon",
        params=GoogleTTSService.InputParams(language=Language.EN_US),
        credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a friendly assistant. Keep answers short and conversational. "
                "You are helping developers to build voice agents quickly. "
                "Generate TTS friendly text. No emojis etc. Keep answers brief. "
                "Don't generate long sentences. Please note that you are a voice assistant."
            ),
        }
    ]
    context = LLMContext(messages)
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
        ),
    )

    pipeline = Pipeline([
        transport.input(),
        stt,
        user_aggregator,
        llm,
        tts,
        transport.output(),
        assistant_aggregator,
    ])

    # Build pipeline params, optionally setting telephony sample rates
    pipeline_params = PipelineParams(enable_metrics=True, enable_usage_metrics=True)
    if audio_sample_rate:
        pipeline_params.audio_in_sample_rate = audio_sample_rate
        pipeline_params.audio_out_sample_rate = audio_sample_rate

    task = PipelineTask(pipeline, params=pipeline_params)

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        messages.append({"role": "system", "content": "Say hello briefly."})
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)
