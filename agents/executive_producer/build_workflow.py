"""Build an inactive synthetic-only n8n candidate; never imports or executes it."""
import argparse
import json
import uuid
from pathlib import Path

from planner import HERE, REPO, build_request, schema


def build():
    request = build_request(REPO / 'contracts/production-manifest/v1.0.0/example.valid.json')
    request['planning_schema'] = schema()

    def node(name, kind, version, parameters, position):
        return {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'fwai-dev-p0201:' + name)),
                'name': name, 'type': kind, 'typeVersion': version,
                'parameters': parameters, 'position': position}

    # A frozen synthetic request cannot be replaced through a webhook/intake.
    prepare = 'return [{json: ' + json.dumps(request) + '}];'
    validate = (HERE / 'validate-plan.js').read_text() + '''
const context = $('Synthetic planning input').first().json;
const items = $input.all();
if (items.length !== 1) throw new Error('Expected one model response');
const response = items[0].json;
// Chain/parser versions can return direct JSON or a structured text/output field.
const plan = response.output ?? response.text ?? response;
if (plan === null || Array.isArray(plan) || typeof plan !== 'object') {
  throw new Error('Structured object response required');
}
validatePlan(plan, context.manifest, context.planning_schema);
return [{json: {
  checkpoint: 'P02.01', is_test: true,
  status: 'candidate_requires_canonical_validation',
  input_manifest: context.input_manifest, candidate: plan,
  blockers: ['Canonical offline validation and real-integration review required'],
  authorization: {production_approved: false, spend_authorized: false, publish_authorized: false},
  dispatch_performed: false
}}];
'''
    nodes = [
        node('Manual synthetic trial', 'n8n-nodes-base.manualTrigger', 1, {}, [0, 0]),
        node('Synthetic planning input', 'n8n-nodes-base.code', 2,
             {'jsCode': prepare, 'mode': 'runOnceForAllItems'}, [240, 0]),
        node('Executive Producer planning', '@n8n/n8n-nodes-langchain.chainLlm', 1.6,
             {'promptType': 'define', 'text': '={{ $json.prompt }}', 'hasOutputParser': True,
              'messages': {'messageValues': [{'message': '={{ $json.system_prompt }}'}]}}, [480, 0]),
        node('Ollama Chat Model - configure locally', '@n8n/n8n-nodes-langchain.lmChatOllama', 1,
             {'model': 'CONFIGURE_EXISTING_LOCAL_MODEL', 'options': {'temperature': 0}}, [360, 240]),
        node('Planning output schema', '@n8n/n8n-nodes-langchain.outputParserStructured', 1.2,
             {'schemaType': 'manual', 'inputSchema': json.dumps(schema()), 'autoFix': False}, [620, 240]),
        node('Validate proposal - no dispatch', 'n8n-nodes-base.code', 2,
             {'jsCode': validate, 'mode': 'runOnceForAllItems'}, [760, 0]),
    ]

    def edge(target, kind='main'):
        return {kind: [[{'node': target, 'type': kind, 'index': 0}]]}

    return {
        'name': 'FWAI-LOCAL — Executive Producer (P02.01 synthetic candidate)',
        'active': False, 'nodes': nodes,
        'connections': {
            'Manual synthetic trial': edge('Synthetic planning input'),
            'Synthetic planning input': edge('Executive Producer planning'),
            'Executive Producer planning': edge('Validate proposal - no dispatch'),
            'Ollama Chat Model - configure locally': edge('Executive Producer planning', 'ai_languageModel'),
            'Planning output schema': edge('Executive Producer planning', 'ai_outputParser'),
        },
        'settings': {'executionOrder': 'v1'}, 'pinData': {}, 'tags': [],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    target = HERE / 'workflow.inactive.json'
    content = json.dumps(build(), indent=2, ensure_ascii=False) + '\n'
    if args.check:
        if target.read_text() != content:
            raise SystemExit('Inactive workflow differs from its reviewed builder')
        print('PASS: inactive workflow matches builder')
    else:
        target.write_text(content)
