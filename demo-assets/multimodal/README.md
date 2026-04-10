# Multimodal Demo Assets

- `voice-sample.mp3`: sample audio clip for microphone/audio upload and ASR smoke checks.
- `vision-sample.jpg`: sample image for image understanding prompts in the unified chat.

Both files are copied from existing repository assets so the demo path stays self-contained in this branch.

## Demo Runbook

Prerequisites:
- `.env` contains a valid MWS key in `OPENAI_API_KEY` or `MWS_API_KEY`.
- Audio STT points to MWS-compatible OpenAI settings from `.env.example`.
- Image generation is enabled and points to an MWS-compatible image model.

Audio file upload:
- Upload `voice-sample.mp3` in the normal chat composer.
- Ask: `Transcribe this audio and summarize it in one sentence.`
- Expected result: the router classifies the attachment as audio, ASR prepends an `[Audio transcript]` block, and the final response is a normal assistant chat message.
- Graceful degradation: without STT access or a supported audio model, the chat should show a clear transcription/access error instead of opening a separate screen.

Microphone recording:
- Click the existing Dictate microphone button in the normal chat composer, record a short phrase, and confirm.
- Ask or auto-send the inserted transcription text.
- Expected result: `VoiceRecording.svelte` records via `MediaRecorder`, calls `transcribeAudio`, inserts returned text into the composer, and the normal chat send path handles the message.
- Graceful degradation: denied microphone permission or missing STT access is shown as a toast/chat error.

Image understanding:
- Upload `vision-sample.jpg` in the normal chat composer.
- Ask: `What is shown in this image? Mention the main visual elements.`
- Expected result: the frontend sends the image as an `image_url` content part, the attachment hint marks it as `vision`, and the router selects a vision-capable VLM when available.
- Graceful degradation: if a manually selected model is not vision-capable, the chat shows `Model <name> is not vision capable` and does not attempt the unsupported request.

Image generation:
- In the normal chat composer, ask: `Generate image: a compact AI workspace dashboard on a sunny desk.`
- Expected result: the router enables `image_generation`, the backend emits a `chat:message:files`/`files` event, and the generated image appears as an assistant message attachment.
- Graceful degradation: without MWS image-generation access or a configured image model, the assistant response should explain that image generation failed and include the underlying access/config error.

Lightweight smoke:
- Run `python3 scripts/smoke-multimodal-contract.py` to verify repository wiring for the three multimodal paths without importing the full backend package.
