# MCP Integration — Decision Memo

> **Audience:** Agent Market hackathon team (decision owners: Shimon as backend lead +
> Chuan for the on-chain attestation tie-in)
> **Status:** Recommendation; team should ratify in the Day-2 / Day-3 sync.
> **Question being decided:** Do we commit to real MCP (Anthropic's Model Context Protocol),
> or do we ship with "MCP-style" homegrown adapters?

## TL;DR

**Commit to real MCP, via [`fastmcp`](https://github.com/jlowin/fastmcp) on the Python side.**
Scope: one demo agent + 2-3 MCP servers (block explorer, defillama, news aggregator) for the
v1 demo. The integration lift is 2-3 person-days and unlocks four pitch-meaningful properties
we cannot get from homegrown adapters.

## What the README currently says

> "Agent Tools: **MCP-style** tool adapters for market data, news, and wallet lookup."

The word "style" is doing a lot of hedging. It allows the team to ship anything that *looks
like* MCP without actually implementing the protocol. The downside of that hedge is what this
memo addresses.

## What MCP actually is

The [Model Context Protocol](https://modelcontextprotocol.io/) is an open protocol developed
by [Anthropic](https://www.anthropic.com/news/model-context-protocol), now adopted broadly,
that standardizes how AI agents discover and invoke tools. Key properties relevant to Agent
Market:

- **Manifest-based tool discovery.** An MCP server publishes a manifest declaring what tools
  it exposes, their signatures, and their semantics. Agents query the manifest to know what
  tools are available before they call any.
- **JSON-RPC over a transport layer.** Standardized message shape, model-agnostic.
- **Wide ecosystem support.** Anthropic Claude, OpenAI's agent SDK, [Eliza](https://github.com/elizaOS/eliza),
  [Swarms](https://github.com/kyegomez/swarms), AutoGen, LangGraph, and many more all
  speak MCP today.
- **Python framework: [fastmcp](https://github.com/jlowin/fastmcp).** Decorator-based API
  similar to FastAPI; minimal boilerplate to expose a Python function as an MCP tool.

## Why real MCP wins against "MCP-style"

### 1. Verifiable tool surface

This is the load-bearing argument. The [agent passport](agent-passport-spec.md) records
which tools an agent had access to during a job. Real MCP makes this auditable:

- The MCP server's manifest is queryable. We can hash it at job time and anchor the hash.
- Future buyers can verify "this agent's tool surface at job time was this set of tools, no
  others."
- The manifest is portable — anyone can run the same MCP server and verify the manifest
  matches.

"MCP-style" adapters don't have a manifest. The tool surface is whatever code the developer
wrote. There is no canonical version to hash; no way to verify the tool surface
independently. This erodes the passport's defensibility.

### 2. Ecosystem compatibility

Real MCP means **any agent built with any MCP-supporting framework can be listed on Agent
Market without rewrites**. The framework-agnostic claim becomes real.

| Framework         | MCP support                                          |
| ----------------- | ---------------------------------------------------- |
| Anthropic Claude  | First-party                                          |
| OpenAI Agents SDK | Supported                                            |
| Eliza             | Supported                                            |
| Swarms            | Native ([per repo description](https://github.com/kyegomez/swarms)) |
| AutoGen           | Supported                                            |
| LangGraph         | Supported                                            |
| Custom Python     | Easy via [fastmcp](https://github.com/jlowin/fastmcp) |

If Agent Market is "MCP-style," none of these agents can be listed without porting work.
That's a marketplace that doesn't fill.

### 3. Cleaner pitch story

Real MCP gives the team a one-line credibility marker: **"We speak MCP, the protocol the AI
industry is converging on."** "MCP-style" is "we have our own adapter standard," which reads
as NIH and reduces pitch credibility.

### 4. Future alignment with x402

Coinbase's [x402](https://docs.cdp.coinbase.com/x402/welcome) protocol has a roadmap item
for `@x402/mcp` — bridging payment-required HTTP semantics with MCP. If/when this ships
stable, MCP-native agents on Agent Market can take advantage of native x402 monetization
patterns directly. "MCP-style" agents cannot.

## What "real MCP" looks like in our stack

### MCP servers (one per data source)

Each external data source we want agents to use becomes a small MCP server. For the v1
demo:

- **`block-explorer-mcp`** — wraps Etherscan / Arbiscan / Arc-explorer APIs. Tools:
  `get_balance`, `get_transactions`, `lookup_token`, etc.
- **`defillama-mcp`** — wraps DeFiLlama API. Tools: `get_protocol_tvl`, `get_token_price`,
  `get_chain_stats`.
- **`news-mcp`** — wraps a news aggregator API (e.g., NewsAPI or a free crypto-specific
  feed). Tools: `search_news`, `get_token_news`.

Each server is a small Python process (~50-100 lines with fastmcp). They expose their
manifests over HTTP or stdio. Total build cost: 1-2 days for one engineer.

### Agent runner integration

The FastAPI backend's job runner calls the agent's framework, which speaks MCP, which calls
the MCP servers. The job runner doesn't need to know which framework the agent uses — only
that it speaks MCP.

```python
# Pseudocode for the job runner
from mcp.client import MCPClient

async def run_job(job_id: str, agent: Agent, user_input: str):
    # Connect MCP servers
    mcp_clients = [MCPClient(url) for url in agent.mcp_server_urls]

    # Compute manifest hash for the passport
    manifests = [c.get_manifest() for c in mcp_clients]
    manifest_hash = keccak256_canonical(manifests)

    # Run the agent with these MCP clients available
    # The agent's framework decides which tools to call
    result, trace = await agent.run(user_input, tools=mcp_clients)

    # Persist trace + tool calls (each tool call should already be logged by the runner)
    persist_passport(job_id, trace, manifest_hash)

    return result
```

The actual implementation will be more careful with error handling and trace capture, but
the shape is roughly this.

### Demo-agent build

For the v1 demo, we need ONE demo agent that fully exercises MCP. Recommendation: build it
as a thin wrapper around an LLM (Claude, GPT-4, etc.) that uses the MCP clients above. The
"agent framework" can literally be 200 lines of Python that:

- Receives a user prompt
- Connects to the MCP servers
- Loops: ask the LLM what to do, call any requested tools, feed results back, repeat
- Returns the final answer + the trace

This is what Anthropic calls a "tool-use agent." There are reference implementations in the
[Claude SDK docs](https://docs.anthropic.com/claude/docs/tool-use).

## Estimated lift

| Component                                    | Owner          | Days  |
| -------------------------------------------- | -------------- | ----- |
| `fastmcp` integration into FastAPI runner    | Shimon         | 1     |
| `block-explorer-mcp` server                  | Daniel R       | 0.5   |
| `defillama-mcp` server                       | Daniel R       | 0.5   |
| `news-mcp` server                            | Önder          | 0.5   |
| Demo agent (LLM + tool-use loop)             | Marten + Dan   | 1     |
| Manifest hashing + passport integration      | Shimon         | 0.5   |
| Math/decision-engine module (Kelly / +EV)    | Önder          | 1     |

**Total: ~3-4 person-days, well-parallelizable.** This fits inside week 1 without
displacing the contract or frontend work.

## What we lose by NOT committing

If we ship with "MCP-style":

- The agent passport's "tool surface" attestation is unverifiable.
- The framework-agnostic claim is weakened.
- The pitch story loses a key credibility marker.
- We can't take advantage of x402 + MCP convergence later.

## What we lose by committing to real MCP

- 0.5-1 day of additional setup vs. a homegrown adapter.
- A learning curve for the team on fastmcp (mitigated by it being well-documented and
  decorator-based).
- A dependency on a third-party library, but `fastmcp` is MIT-licensed, actively maintained,
  and has a clear deprecation/breaking-change policy.

The downsides are real but small. The upsides are pitch-meaningful and architectural.

## Open questions

1. **Which transport?** HTTP is the easier choice for v1. Stdio is more efficient but harder
   to deploy. **Recommendation: HTTP for v1.**
2. **Do we run MCP servers as separate processes or import them as Python modules?**
   Separate processes are more faithful to the protocol; modules are easier to deploy.
   **Recommendation: separate processes in Docker compose; matches production patterns.**
3. **Do we expose our MCP servers publicly, or are they platform-internal?**
   **Recommendation: platform-internal for v1.** Public exposure is a v2 conversation
   (and a potential business model).
4. **Should the platform itself expose an MCP server?** (e.g., for agent-to-agent commerce
   on Agent Market.) **Recommendation: yes, in v2, not v1.**

## Decision

**Commit to real MCP via fastmcp.** Plan the work as outlined above.

If the team wants to challenge this, the burden of proof is:

- Demonstrate a specific MCP-incompatibility blocker we can't solve in 1 day.
- Demonstrate a measurable pitch advantage of "MCP-style" we can't get any other way.

Neither of these is likely. The recommendation stands.
