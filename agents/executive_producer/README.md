# P02.01 Executive Producer development candidate

Status: **implemented and tested with synthetic model responses; real integration
and owner acceptance pending**. This directory does not close P02.01. P02.02 and
later checkpoints have not been started. The locked checklist and accepted
contract/checkpoint records are unchanged.

`planner.py` reads an exact canonical manifest, verifies accepted contract hashes,
prepares an Ollama prompt, checks a proposed work breakdown, and wraps a valid
candidate in the existing P01.02 contract. It has no model client, network calls,
tools, file-writing methods, workflow dispatch or receipt resolver. Every result
remains `blocked`, with all authorization flags false. `validation: passed` means
the deterministic shape/identity/dependency checks passed, not that content was
researched, a model ran or an owner approved it.

The role-specific development profile adds package IDs, stage assignments,
dependencies and explicit gate descriptions within the native P01.02 payload.
It does not amend v1.0.0 contracts. Seven proposed work packages cover research,
script, visuals, avatar, budget, assembly and QC; their directed dependencies are
checked for missing references and cycles. These are planning handoffs, not
executed delegation or a P03 orchestrator. The baseline registry ID identifies
the logical reference role and does not authenticate a new workflow or sender.

## Offline checks

From this isolated checkout:

```sh
sh agents/executive_producer/run-isolated-tests.sh
```

Prerequisites already available in this session: Python 3.12 with `jsonschema`,
`/usr/bin/node` and Bubblewrap with user/network namespaces permitted. No package
installation is performed. If namespace setup fails, stop; there is no fallback to
running tests against the host network. The runner exposes only system binaries,
libraries and read-only source. It does not mount production home, credentials,
Docker sockets, databases, volumes or service networks. Namespace loopback is
separate from the host. Private temporary space is ephemeral.

The tests verify canonical input/output compatibility, revision byte hashes,
rejection of seven invalid canonical manifests, malformed model plans, unknown
roles, duplicate packages, graph cycles, missing gates, permission injection,
unique attempt IDs, CLI behavior and Python/JavaScript validator agreement.
JavaScript tests run actual candidate Code-node source with mocked n8n item APIs;
they do not run an n8n engine or simulate real Ollama quality. Environment and
filesystem/network isolation are checked in that same suite.

The CLI supports `request --manifest PATH` and
`evaluate --manifest PATH --response PATH`; it prints JSON and writes no files.
Inputs must resolve inside this checkout. Use synthetic fixtures only. For a
candidate workflow result, pass its `candidate` field to `evaluate`; the wrapper
is intentionally not itself an accepted `agent_result`.

## Inactive workflow

`workflow.inactive.json` contains a manual trigger, a frozen synthetic input,
Basic LLM Chain, Ollama Chat Model, Structured Output Parser and deterministic
proposal validation. It has no credentials, real workflow ID, HTTP/webhook/tool
nodes, database operations or outgoing dispatch. It is inactive. Its model is an
explicit configuration placeholder, not a model substitution or download request.
Neither this file nor any other workflow was imported or executed in this session.

`build_workflow.py` regenerates the candidate deterministically;
`build_workflow.py --check` verifies it without writing. The Code-node validator
implements only the schema keywords used by the reviewed planning profile; it is
not a general JSON Schema engine or replacement for the P01 Python validator.
Changing the profile requires matching Python/JavaScript tests. A structurally
valid response exits as `candidate_requires_canonical_validation`, with false
authorization and no dispatch. Parser/model errors stop the chain; there is no
automatic repair, fallback provider or retry configured in this artifact.

The node layout and parameter names were checked against upstream n8n sources:
[Basic LLM Chain](https://github.com/n8n-io/n8n/blob/master/packages/%40n8n/nodes-langchain/nodes/chains/ChainLLM/ChainLlm.node.ts),
[chain parameters](https://github.com/n8n-io/n8n/blob/master/packages/%40n8n/nodes-langchain/nodes/chains/ChainLLM/methods/config.ts),
[Ollama Chat Model](https://github.com/n8n-io/n8n/blob/master/packages/%40n8n/nodes-langchain/nodes/llms/LMChatOllama/LmChatOllama.node.ts),
and [Structured Output Parser](https://github.com/n8n-io/n8n/blob/master/packages/%40n8n/nodes-langchain/nodes/output_parser/OutputParserStructured/OutputParserStructured.node.ts).
These are moving upstream references consulted on November 13, 2026, not the
installed production version. Real import/parameter compatibility is unverified.

## Acceptance gate still open

An authorized operator must first identify an isolated n8n development instance,
its installed node versions, and an existing local Ollama model. Do not change a
production credential to configure this candidate. Readiness, connectivity,
inference, malformed-response behavior and content quality need controlled real
tests. Preserve full input, raw response, canonical validation findings and model
version evidence without credentials or runtime data in Git. A model's claim of
approval or executed work is untrusted text, even when its shape passes validation.

The owner must review useful delegation, blocker handling and the proposed
role-validation profile. If deployment needs a new instance ID, review the pinned
registry/version migration separately; do not impersonate the baseline workflow.
Do not advance to P02.02 while P02.01 acceptance remains unavailable.
