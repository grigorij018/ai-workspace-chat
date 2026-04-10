import unittest
from types import SimpleNamespace

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


if __name__ == '__main__':
    unittest.main()
