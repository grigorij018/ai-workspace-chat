#!/usr/bin/env python3
"""Lightweight multimodal wiring smoke check.

This intentionally avoids importing ``open_webui`` because the local dev
environment may not have all backend dependencies installed. It verifies the
repo wiring that keeps multimodal flows inside the unified chat pipeline.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CHECKS = [
    (
        "audio upload -> ASR -> text chat path",
        "backend/open_webui/orchestrator/router.py",
        [
            "def maybe_transcribe_audio",
            "from open_webui.routers.audio import transcribe",
            "[Audio transcript]",
            "form_data['model'] = text_model",
        ],
    ),
    (
        "microphone recording -> transcription hook",
        "src/lib/components/chat/MessageInput/VoiceRecording.svelte",
        [
            "navigator.mediaDevices.getUserMedia",
            "new MediaRecorder",
            "transcribeAudio(",
            "onConfirm(res)",
        ],
    ),
    (
        "image upload + question -> VLM content path",
        "src/lib/components/chat/Chat.svelte",
        [
            "type: 'image_url'",
            "routing_intent = 'vision'",
            "attachment_hints: buildAttachmentHints",
            "manual_override: model.id",
        ],
    ),
    (
        "text prompt -> image generation -> assistant attachment",
        "backend/open_webui/utils/middleware.py",
        [
            "async def chat_image_generation_handler",
            "'type': 'files'",
            "_serialize_generated_files(images)",
            "'content_type': image.get('content_type', 'image/png')",
        ],
    ),
    (
        "generated image attachments include metadata",
        "backend/open_webui/routers/images.py",
        [
            "def build_generated_image_attachment",
            "'id': _read_file_item_value(file_item, 'id')",
            "'content_type': content_type",
        ],
    ),
    (
        "contract documents attachment hints",
        "docs/CONTRACTS.md",
        [
            "metadata.attachment_hints",
            "transcription_requested",
            "Assistant-side image generation returns generated image files as normal chat message attachments",
        ],
    ),
    (
        "demo assets runbook exists",
        "demo-assets/multimodal/README.md",
        [
            "voice-sample.mp3",
            "vision-sample.jpg",
            "Expected result",
        ],
    ),
]


def main() -> int:
    failures: list[str] = []
    for label, rel_path, needles in CHECKS:
        path = ROOT / rel_path
        text = path.read_text()
        missing = [needle for needle in needles if needle not in text]
        if missing:
            failures.append(f"{label}: {rel_path} missing {missing}")

    if failures:
        print("Multimodal smoke check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Multimodal smoke check passed ({len(CHECKS)} checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
