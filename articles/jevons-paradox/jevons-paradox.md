---
title: "LangGraph 1.0 Released: No Breaking Changes, All the Hard-Won Lessons"
subtitle: "Production-ready agent orchestration that companies like Uber and LinkedIn already depend on"
tags: [ai, langgraph, python, agents, production]
canonical_url: ""
cover: "./images/cover.png"
updated: "2025-10-25"
---

# LangGraph 1.0 Released: No Breaking Changes, All the Hard-Won Lessons
> LangGraph 1.0 just shipped. Zero breaking changes. It's the stabilization of the runtime that big companies already depend on in production.

LangGraph is a low-level agent orchestration framework. It gives you fine-grained control over agent workflows through a graph abstraction: nodes (functions), edges (control flow), and state (what gets passed around).

Unlike high-level agent libraries that make decisions for you, LangGraph gives you the primitives to build exactly what you need.

---

## LangGraph 1.0 is a maturity story, not a feature drop

The *low-level* label undersells it. LangGraph isn't just a state machine library, it's an agent runtime with production features built in. This 1.0 release is about **stability**, not flashy features. The core graph primitives: state, nodes, edges, remain unchanged.

### The Hard-Won Lessons: Why LangGraph Exists

When LangChain launched in late 2022, the goal was radical simplicity: RAG in five lines of code, SQL queries in three. The barrier to entry was stupidly low, and that's what the ecosystem needed. Developers could prototype agent ideas in an afternoon.

But *easy to start* came with a cost. Early LangChain made assumptions to keep things simple: hidden prompts, implicit context engineering, pre-configured chains that did useful things but were opaque when you needed to customize them.

**The controllability wall hit hard.** You'd build a working prototype, then try to add authentication, or custom error handling, or dynamic model selection based on user context. Suddenly you're fighting the framework instead of using it.

**The reliability gap hit hard.** LLMs are capable, they can reason, use tools, write code. But capable doesn't mean reliable at scale. When you're running agents for thousands of concurrent users, or agents that need to run for hours or days, the fragility shows up fast.

**LangGraph was built to bridge this gap.** Give developers full control over agent workflows without forcing them to reinvent persistence, streaming, and state management. Let them define exactly what their agent does while the runtime handles the production concerns that are hard to get right.

The result is a framework where the floor is lower than you'd expect (graph definitions are surprisingly readable) and the ceiling is essentially unlimited (you can build arbitrarily complex workflows).

### The Runtime That Ships to Production

LangGraph 1.0 stabilizes four core runtime features that separate production agents from demos:

- **Durable Execution**. Your agent is three steps into a ten-step workflow when the server restarts. With LangGraph, it picks up exactly where it left off. Checkpointing saves state at every node execution. No lost work. No starting over. This works for agents that run for hours or days.

- **Streaming**. LangGraph streams everything: LLM tokens, tool calls, state updates, node transitions. Users see progress in real-time. An agent that takes 30 seconds to respond feels broken unless users can see it working.

- **Human-in-the-Loop**. Prototyping human oversight is trivial—just add an `input()` prompt. Scaling it is hard. LangGraph's runtime pauses execution, saves state, and waits for human input without blocking threads. When the human responds (seconds or hours later), execution resumes from the exact point it paused. This works whether you have one user in a terminal or ten thousand in a web UI.

- **Memory**. Short-term memory (working context) is built into state management. Long-term memory (across sessions) uses persistent checkpointers that plug into databases. Your agent's state is the memory. Checkpoint = save. Resume = load.

---

## LangChain 1.0 is built on LangGraph

LangChain 1.0 has launched alongside LangGraph 1.0, and the two releases are deeply intertwined.

It's easy to assume LangChain is the foundation and LangGraph is an extension. It's the opposite. LangGraph is the low-level runtime, and LangChain is now a high-level API built on that runtime.

### create_agent: The New Standard

The centerpiece of LangChain 1.0 is [`create_agent`](https://docs.langchain.com/oss/python/releases/langchain-v1), the new standard for building agents.

This replaces `langgraph.prebuilt.create_react_agent` (now deprecated). Same high-level interface with little tweaks to make it easier to understand.

What this creates is what I like to call a "unitary" agent, an llm with access to tools, that given an input decides which tools to call to provide a response. Typically this is a point of indeterminism and agency in the system. It uses the (ReAct)[https://research.google/blog/react-synergizing-reasoning-and-acting-in-language-models/] architecture.

<img src="./assets/reactagent.gif" alt="Unitary Agent" width="300">

*Example of a unitary agent with two tools, using the ReAct architecturee*

### Middleware: The Defining Feature

The controllability problem that drove developers to LangGraph—needing fine-grained control over agent behavior—now has a solution that doesn't require dropping down to graph definitions.

**Middleware** lets you inject logic at any point in the agent loop: before/after the LLM call, around tool execution, before/after the entire agent run. It's the customization escape hatch that raises the ceiling without complicating the floor.

LangChain ships with prebuilt middleware for common patterns like PII (Personally Identifiable Information) detection, summarization, and human in the loop, but you can also build your own, for example to switch models based on user context.


### Standard Content Blocks: Provider-Agnostic LLM Outputs

One more quiet but important addition: **standard content blocks.**

LLM providers now return complex structured outputs: reasoning traces (Claude's thinking), built-in tool calls, citations, web search results, code execution outputs. Each provider formats these differently.

LangChain 1.0 introduces [`.content_blocks`](https://docs.langchain.com/oss/python/releases/langchain-v1#standard-content-blocks)—a standard representation for message content that works across providers.

## Which should I use? LangChain vs LangGraph

Start with LangChain. The `create_agent` primitive gives you a working agent in a few lines, and middleware lets you customize without leaving the high-level API.

**Move to LangGraph when you need orchestration.** If your workflow combines deterministic steps and agentic behavior, or you're building complex multi-agent systems, LangGraph is the right tool for orchestration.

The key insight: **you don't have to choose**. Use LangGraph for orchestration, while using LangChain primitives inside the nodes for LLM interactions, tools, and agent primitives. They're complementary, not alternatives.

Most production systems aren't 100% agentic (LLM decides everything) or 100% deterministic (predefined steps). They're a mix—some branches follow fixed logic, others let the LLM decide. LangGraph lets you model this explicitly while LangChain handles the agent primitives. The [Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph) guide walks through this mental model.

## One last thing: documentation

The 1.0 release includes a complete documentation overhaul. Both LangChain and LangGraph docs have been completely rewritten with more examples, better structure, and easier to navigate. A big improvement over the previous experience as a developer working with the frameworks.

---

*P.S. Sorry. If I'd had more time, this article would be shorter.*

---

**Links:**
- [Video conversation between LangChain developers about the release](https://www.youtube.com/watch?v=r5Z_gYZb4Ns)
- [LangGraph 1.0 announcement](https://blog.langchain.com/langchain-langchain-1-0-alpha-releases/)
- [LangChain 1.0 docs](https://docs.langchain.com/oss/python/releases/langchain-v1)
- [LangGraph 1.0 docs](https://docs.langchain.com/oss/python/releases/langgraph-v1)
- [Thinking in LangGraph guide](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)
- [Middleware deep dive](https://docs.langchain.com/oss/python/releases/langchain-v1#middleware)
