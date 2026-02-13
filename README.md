# Voice AI Agent — Quick Starter

A minimal, production-ready Voice AI Agent built with [Pipecat](https://github.com/pipecat-ai/pipecat) that wires up **Google Cloud STT + Gemini LLM + Google Cloud TTS** into a conversational voice pipeline — over both **WebRTC** (browser) and **Exotel telephony** (phone calls).

## What This Agent Does

- **Speech-to-Text**: Google Cloud STT (Chirp 3) for accurate real-time transcription
- **LLM**: Google Gemini 2.5 Flash Lite via Vertex AI for fast, conversational responses
- **Text-to-Speech**: Google Cloud TTS (Chirp3-HD) for natural-sounding voice output
- **WebRTC**: Talk to the agent directly from your browser
- **Exotel Telephony**: Receive phone calls and converse via Exotel's WebSocket streaming
- **Voice Activity Detection**: Silero VAD for natural turn-taking (200ms stop threshold)
- **Metrics**: Built-in pipeline and usage metrics

## Architecture

```
┌──────────┐     ┌─────────┐     ┌───────────┐     ┌─────────┐     ┌──────────┐
│  Audio   │────>│ Google  │────>│  Gemini   │────>│ Google  │────>│  Audio   │
│  Input   │     │ STT     │     │  LLM      │     │ TTS     │     │  Output  │
└──────────┘     └─────────┘     └───────────┘     └─────────┘     └──────────┘
   WebRTC         Chirp 3        Flash Lite 2.5     Chirp3-HD        WebRTC
   or Exotel                     (Vertex AI)                        or Exotel
```

## Project Structure

```
voicebot-quick-starter/
├── bot.py              # Core pipeline: STT → LLM → TTS
├── default_runner.py   # WebRTC runner — browser-based voice chat
├── exotel_runner.py    # Exotel runner — telephony via WebSocket
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not committed)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Quick Start

### Prerequisites

- Python 3.10+
- A Google Cloud project with the following APIs enabled:
  - Cloud Speech-to-Text API
  - Vertex AI API
  - Cloud Text-to-Speech API
- A GCP service account JSON key file

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/exotel/voicebot-quick-starter.git
   cd voicebot-quick-starter
   ```

2. **Set up Python environment with micromamba:**

   Install micromamba (one-time setup):

   ```bash
   "${SHELL}" <(curl -L micro.mamba.pm/install.sh)
   ```

   The installer will ask a few questions — accept the defaults:

   | Prompt | What to enter |
   |--------|---------------|
   | Micromamba binary folder? `[~/.local/bin]` | Press **Enter** |
   | Init shell (bash)? `[Y/n]` | Type **Y**, press **Enter** |
   | Configure conda-forge? `[Y/n]` | Type **Y**, press **Enter** |
   | Prefix location? `[~/micromamba]` | Press **Enter** |

   Then reload your shell and create the environment:

   ```bash
   source ~/.bashrc

   micromamba create -n dev_conf python=3.12 -c conda-forge
   micromamba activate dev_conf
   ```

3. **Install dependencies:**

   Run from the `voicebot-quick-starter/` directory:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**

   Create a `.env` file inside the `voicebot-quick-starter/` directory:

   ```bash
   # Google Cloud credentials (STT, LLM, TTS)
   GOOGLE_APPLICATION_CREDENTIALS=./your-service-account.json
   ```

   Place your GCP service account JSON file in the same `voicebot-quick-starter/` directory and update the path accordingly.

### Running the Agent

#### Option 1: WebRTC (Browser)

Run from the `voicebot-quick-starter/` directory:

```bash
python default_runner.py
```

Open **http://localhost:7860/client** in your browser and click **Connect**.

#### Option 2: Exotel Telephony

Running the Exotel runner locally requires a public URL so that Exotel can reach your machine. Set up ngrok first — see [ngrok Setup](#ngrok-setup) below.

Once ngrok is running, start the agent from the `voicebot-quick-starter/` directory:

```bash
python exotel_runner.py
```

The agent starts a WebSocket server ready to accept Exotel voice streams at 8kHz.

To place a call that connects your phone to the agent, use the Exotel Connect API:

```bash
curl -k -X POST \
  'https://<API_KEY>:<API_TOKEN>@api.exotel.com/v1/Accounts/<ACCOUNT_SID>/Calls/connect.json' \
  -F 'StreamType=bidirectional' \
  -F 'StreamUrl=<NGROK_PUBLIC_URL>/ws' \
  -F 'From=<YOUR_PHONE_NUMBER>' \
  -F 'CallerId=<YOUR_EXOPHONE>' \
  -F 'Record=true'
```

Replace the placeholders:

| Placeholder | Description |
|-------------|-------------|
| `<API_KEY>:<API_TOKEN>` | Your Exotel API credentials (found in the Exotel dashboard) |
| `<ACCOUNT_SID>` | Your Exotel account SID |
| `<NGROK_PUBLIC_URL>` | The public URL from ngrok (e.g., `wss://abcd1234.ngrok-free.app`) |
| `<YOUR_PHONE_NUMBER>` | The phone number that will receive the call |
| `<YOUR_EXOPHONE>` | The Exophone (virtual number) you purchased from Exotel |

You'll receive a call on your phone — once you pick up, you'll be talking to the agent.

## ngrok Setup

ngrok exposes your local server to the internet, which is required for the Exotel runner to receive incoming voice streams.

1. Install ngrok by following the steps at [https://ngrok.com/download](https://ngrok.com/download)
2. Add your authtoken (sign up for a free account at [ngrok.com](https://ngrok.com) if you don't have one):

   ```bash
   ngrok config add-authtoken <your-authtoken>
   ```

3. Expose your local server:

   ```bash
   ngrok http 7860
   ```

4. Copy the public `https://` URL from the ngrok output — use this as the `<NGROK_PUBLIC_URL>` in the Exotel curl command above (replace `https://` with `wss://` and append `/ws`).

## Google Cloud Setup

1. Create a GCP project and enable the required APIs:
   - Cloud Speech-to-Text API
   - Vertex AI API
   - Cloud Text-to-Speech API
2. Create a service account with the following roles:
   - `roles/speech.client` — Speech-to-Text
   - `roles/aiplatform.user` — Vertex AI (Gemini LLM)
3. Download the service account JSON key
4. Place the JSON file inside the `voicebot-quick-starter/` directory
5. Set `GOOGLE_APPLICATION_CREDENTIALS` in `voicebot-quick-starter/.env` to point to it

## Customizing the Agent

Edit `voicebot-quick-starter/bot.py` to customize:

- **System prompt** — Change the agent's personality and behavior
- **STT region** — Currently set to `asia-south1` (Mumbai)
- **STT model** — Currently using `chirp_3`
- **LLM model** — Currently using `gemini-2.5-flash-lite`; swap for other Gemini models as needed
- **TTS voice** — Currently using `en-US-Chirp3-HD-Charon`; see [available voices](https://cloud.google.com/text-to-speech/docs/chirp3-hd)
- **VAD sensitivity** — Adjust `stop_secs` in `VADParams` for turn-taking timing

### Swap in Your Preferred STT, LLM, or TTS

Pipecat supports a wide range of providers. You can replace any component in the pipeline by swapping the service class in `bot.py`. Refer to the examples in the Pipecat repo for guidance:

| Component | Supported Providers | Examples |
|-----------|-------------------|----------|
| **STT** | Deepgram, AssemblyAI, Whisper, Azure, Google | [STT examples](https://github.com/pipecat-ai/pipecat/tree/main/examples/foundational) |
| **LLM** | OpenAI, Anthropic, Google Gemini, Azure, Groq | [LLM examples](https://github.com/pipecat-ai/pipecat/tree/main/examples/foundational) |
| **TTS** | Cartesia, ElevenLabs, PlayHT, Deepgram, Google, Azure | [TTS examples](https://github.com/pipecat-ai/pipecat/tree/main/examples/foundational) |

For the full list of supported services, see the [Pipecat services documentation](https://docs.pipecat.ai/server/services/overview).

## Deployment

### Production

Deploy to any cloud provider (GCP, AWS, etc.) and ensure:

- WebSocket connections are supported by your load balancer
- The GCP service account JSON is securely mounted (not baked into the image)
- Environment variables are injected via a secrets manager

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | [Pipecat](https://github.com/pipecat-ai/pipecat) v0.0.101 |
| STT | Google Cloud Speech-to-Text (Chirp 3) |
| LLM | Google Gemini 2.5 Flash Lite (Vertex AI) |
| TTS | Google Cloud Text-to-Speech (Chirp3-HD) |
| VAD | Silero VAD |
| WebRTC | Pipecat SmallWebRTC |
| Telephony | Exotel WebSocket Streaming |

## Troubleshooting

### No Audio Output

- Ensure your browser allows microphone access (WebRTC mode)
- Check that `GOOGLE_APPLICATION_CREDENTIALS` in `voicebot-quick-starter/.env` points to a valid service account JSON
- Review the terminal logs for `ErrorFrame` messages

### High Latency

- Adjust `stop_secs` in VAD params — lower values mean faster turn-taking but may cut off speech

### Exotel Connection Issues

- Verify ngrok is running and the WebSocket URL is publicly accessible (see [ngrok Setup](#ngrok-setup))

## License

MIT

## Acknowledgments

- [Pipecat](https://github.com/pipecat-ai/pipecat) — Open-source framework for voice and multimodal AI agents
- [Exotel](https://www.exotel.com) — Cloud telephony and voice streaming
- [Google Cloud](https://cloud.google.com/) — STT, LLM, and TTS services
