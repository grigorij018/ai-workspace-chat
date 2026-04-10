import unittest
import unittest.mock
from types import SimpleNamespace

from fastapi import HTTPException

from open_webui.orchestrator.registry import apply_capabilities, infer_capabilities
from open_webui.orchestrator.router import ROUTER_MODEL_ID, route_chat_request


def _build_request(models: dict):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(MODELS=models)))


class RouterTests(unittest.TestCase):
    def test_infer_capabilities_for_multimodal_and_embeddings_models(self):
        vision_caps = infer_capabilities({'id': 'gpt-4.1', 'name': 'GPT-4.1'})
        embedding_caps = infer_capabilities({'id': 'text-embedding-3-large', 'name': 'Embedding'})
        image_caps = infer_capabilities({'id': 'gpt-image-1', 'name': 'Image Gen'})

        self.assertTrue(vision_caps['vision'])
        self.assertTrue(embedding_caps['embeddings'])
        self.assertFalse(embedding_caps['text'])
        self.assertTrue(image_caps['image_generation'])

    def test_route_chat_request_uses_web_research_for_latest_queries(self):
        models = {
            ROUTER_MODEL_ID: apply_capabilities({'id': ROUTER_MODEL_ID, 'name': 'Router', 'info': {'meta': {}}}),
            'gpt-4.1-mini': apply_capabilities({'id': 'gpt-4.1-mini', 'name': 'GPT-4.1 Mini', 'info': {'meta': {}}}),
            'gpt-image-1': apply_capabilities({'id': 'gpt-image-1', 'name': 'GPT Image', 'info': {'meta': {}}}),
        }
        request = _build_request(models)

        form_data = {
            'model': ROUTER_MODEL_ID,
            'messages': [{'role': 'user', 'content': 'Find the latest AI research news'}],
        }
        metadata = {}

        updated_form_data, updated_metadata, routed_model, decision = route_chat_request(
            request, form_data, SimpleNamespace(id='user-1'), metadata, models[ROUTER_MODEL_ID]
        )

        self.assertEqual(decision.task_type, 'web_research')
        self.assertEqual(decision.selected_tool, 'web_research')
        self.assertTrue(updated_form_data['features']['web_search'])
        self.assertEqual(routed_model['id'], 'gpt-4.1-mini')
        self.assertEqual(updated_metadata['selected_model_id'], 'gpt-4.1-mini')

    def test_route_chat_request_uses_deep_research_mode(self):
        models = {
            ROUTER_MODEL_ID: apply_capabilities({'id': ROUTER_MODEL_ID, 'name': 'Router', 'info': {'meta': {}}}),
            'gpt-4.1-mini': apply_capabilities({'id': 'gpt-4.1-mini', 'name': 'GPT-4.1 Mini', 'info': {'meta': {}}}),
        }
        request = _build_request(models)

        form_data = {
            'model': ROUTER_MODEL_ID,
            'messages': [{'role': 'user', 'content': 'Deep research: compare RAG approaches'}],
        }
        metadata = {}

        updated_form_data, updated_metadata, _, decision = route_chat_request(
            request, form_data, SimpleNamespace(id='user-1'), metadata, models[ROUTER_MODEL_ID]
        )

        self.assertEqual(decision.task_type, 'deep_research')
        self.assertEqual(decision.selected_tool, 'deep_research')
        self.assertTrue(updated_form_data['features']['web_search'])
        self.assertTrue(updated_form_data['features']['deep_research'])
        self.assertEqual(updated_metadata['selected_model_id'], 'gpt-4.1-mini')

    def test_route_chat_request_uses_pptx_generation(self):
        models = {
            ROUTER_MODEL_ID: apply_capabilities({'id': ROUTER_MODEL_ID, 'name': 'Router', 'info': {'meta': {}}}),
            'gpt-4.1-mini': apply_capabilities({'id': 'gpt-4.1-mini', 'name': 'GPT-4.1 Mini', 'info': {'meta': {}}}),
        }
        request = _build_request(models)

        form_data = {
            'model': ROUTER_MODEL_ID,
            'messages': [{'role': 'user', 'content': 'Собери презентацию по текущему диалогу'}],
        }
        metadata = {}

        updated_form_data, _, _, decision = route_chat_request(
            request, form_data, SimpleNamespace(id='user-1'), metadata, models[ROUTER_MODEL_ID]
        )

        self.assertEqual(decision.task_type, 'pptx_generation')
        self.assertEqual(decision.selected_tool, 'pptx_generation')
        self.assertTrue(updated_form_data['features']['pptx_generation'])

    def test_route_chat_request_respects_manual_override(self):
        models = {
            ROUTER_MODEL_ID: apply_capabilities({'id': ROUTER_MODEL_ID, 'name': 'Router', 'info': {'meta': {}}}),
            'gpt-4.1-mini': apply_capabilities({'id': 'gpt-4.1-mini', 'name': 'GPT-4.1 Mini', 'info': {'meta': {}}}),
            'gpt-4.1': apply_capabilities({'id': 'gpt-4.1', 'name': 'GPT-4.1', 'info': {'meta': {}}}),
        }
        request = _build_request(models)

        form_data = {
            'model': ROUTER_MODEL_ID,
            'messages': [{'role': 'user', 'content': 'Hello'}],
        }
        metadata = {'manual_override': 'gpt-4.1'}

        updated_form_data, updated_metadata, _, decision = route_chat_request(
            request, form_data, SimpleNamespace(id='user-1'), metadata, models[ROUTER_MODEL_ID]
        )

        self.assertTrue(decision.manual_override)
        self.assertEqual(decision.selected_model, 'gpt-4.1')
        self.assertEqual(updated_form_data['model'], 'gpt-4.1')
        self.assertTrue(updated_metadata['manual_override'])

    def test_route_chat_request_detects_url_pipeline(self):
        models = {
            ROUTER_MODEL_ID: apply_capabilities({'id': ROUTER_MODEL_ID, 'name': 'Router', 'info': {'meta': {}}}),
            'gpt-4.1-mini': apply_capabilities({'id': 'gpt-4.1-mini', 'name': 'GPT-4.1 Mini', 'info': {'meta': {}}}),
        }
        request = _build_request(models)

        form_data = {
            'model': ROUTER_MODEL_ID,
            'messages': [{'role': 'user', 'content': 'Summarize https://example.com/article'}],
        }
        metadata = {}

        updated_form_data, _, _, decision = route_chat_request(
            request, form_data, SimpleNamespace(id='user-1'), metadata, models[ROUTER_MODEL_ID]
        )

        self.assertEqual(decision.task_type, 'url')
        self.assertEqual(decision.selected_tool, 'url_parse')
        self.assertEqual(updated_form_data['files'][0]['type'], 'url')

    def test_route_chat_request_preserves_attachment_hints_from_audio_files(self):
        models = {
            ROUTER_MODEL_ID: apply_capabilities({'id': ROUTER_MODEL_ID, 'name': 'Router', 'info': {'meta': {}}}),
            'gpt-4.1-mini': apply_capabilities({'id': 'gpt-4.1-mini', 'name': 'GPT-4.1 Mini', 'info': {'meta': {}}}),
        }
        request = _build_request(models)

        form_data = {
            'model': ROUTER_MODEL_ID,
            'messages': [{'role': 'user', 'content': 'Transcribe this'}],
            'files': [{'id': 'file-audio-1', 'name': 'note.webm', 'content_type': 'audio/webm'}],
        }
        metadata = {'attachment_hints': [{'name': 'note.webm', 'content_type': 'audio/webm'}]}

        with unittest.mock.patch(
            'open_webui.orchestrator.router._get_audio_file_path', return_value='/tmp/note.webm'
        ), unittest.mock.patch(
            'open_webui.orchestrator.router.maybe_transcribe_audio',
            return_value={'model': 'gpt-4.1-mini', 'messages': form_data['messages'], 'files': form_data['files']},
        ):
            updated_form_data, updated_metadata, _, decision = route_chat_request(
                request, form_data, SimpleNamespace(id='user-1'), metadata, models[ROUTER_MODEL_ID]
            )

        self.assertEqual(decision.task_type, 'audio')
        self.assertEqual(updated_form_data['model'], 'gpt-4.1-mini')
        self.assertEqual(updated_metadata['attachment_hints'][0]['modality'], 'audio')
        self.assertTrue(updated_metadata['attachment_hints'][0]['transcription_requested'])

    def test_route_chat_request_rejects_manual_override_without_vision(self):
        models = {
            ROUTER_MODEL_ID: apply_capabilities({'id': ROUTER_MODEL_ID, 'name': 'Router', 'info': {'meta': {}}}),
            'gpt-4.1-mini': apply_capabilities({'id': 'gpt-4.1-mini', 'name': 'GPT-4.1 Mini', 'info': {'meta': {}}}),
        }
        request = _build_request(models)

        form_data = {
            'model': ROUTER_MODEL_ID,
            'messages': [{'role': 'user', 'content': 'What is on this image?'}],
            'files': [{'id': 'file-image-1', 'name': 'photo.png', 'content_type': 'image/png', 'type': 'image'}],
        }
        metadata = {'manual_override': 'gpt-4.1-mini'}

        with self.assertRaises(HTTPException) as exc:
            route_chat_request(request, form_data, SimpleNamespace(id='user-1'), metadata, models[ROUTER_MODEL_ID])

        self.assertEqual(exc.exception.status_code, 400)
        self.assertIn('does not support image understanding', exc.exception.detail)


if __name__ == '__main__':
    unittest.main()
