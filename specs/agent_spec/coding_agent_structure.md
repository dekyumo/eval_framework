# Foreword

This document reports on the structure of open source coding agent frameworks. Its goal is to borrow the structure of those coding agents to implement an agentic loop inside random software.

# Part 1: the UI

The UI connects the coding agent to the agentic core. It generally has the following parts:

- a switch between the different UIs
    - chat protocols telegram/discord/slack/... (one discoverable plugin per chat protocol)
    - TUI
    - command line chat
    - CLI
    - cronjob CLI
    - local web interface
    - A2A or ACP protocols

- protocols:
    - Google's AG-UI protocol: message parts, reasoning start/stop, tool use start/stop, agent start/stop, stop button, support for re-synchro after disconnection/chunks for streaming
    - ACP protocol: transmits message parts
    - pi's interface: parts, state update, tool start/stop, response start/stop
    - openclaw's gateway protocol: https://github.com/openclaw/openclaw/tree/main/packages/gateway-protocol/src/schema

Source locations:
- Hermes: https://github.com/NousResearch/hermes-agent/
    - web: /web/ (a straightforward implementation, pages for model picking, oauth, skills and commands edition, mcp params, crons, analytics)
    - desktop: /apps/desktop/src/
    - tui: /ui-tui/ (components for progress display, session, turn history, reasoning display, subagents, clipboard, hotkeys, path display, usage, metrics)
    - cli: /hermes_cli/ (components for clipboard, auth, cron, goal setting to keep intent on long tasks, memory, mcp, model catalog/switching, conversation history, secrets, skills, tools)
- Gemini agent: https://github.com/google-gemini/gemini-cli
    - shared: packages/cli/ shares the CLI and webui code to connect to the Gemini agent core
    - web: packages/cli/src/ui
    - cli: handles client side auth/mcp/skills/settings/slash commands
- Open Claw: https://github.com/openclaw/openclaw
    - terminal: /packages/terminal-core/  a simple terminal
    - gateway: /packages/gateway-protocol/ and /packages/gateway-client/, since OpenClaw connects to many chat interfaces and not agent UI/TUI, the protocol is simple, implementations are in /extensions/
    - apps: /apps/, apps for android, ios, macos
    - gateway: /packages/gateway-protocol and /packages/gateway-client for interfaces, /src/gateway/ for abstract implem, /extensions/ for implementations of various chat surfaces
- core concept:
    - a gateway connects to an agent endpoint, sends configs (for example, all the config in the cursor settings page), receives a list of chat sessions and running agents
    - after this initial setup, it receives (usually async/streaming) updates on the various chat sessions

# Part 2: The Loop

An agentic loop (more precisely a software development agentic loop) could defined as:

while True:
    user_input = input()
    messages.append(user_input)

    llm = LLM(params)

    response = llm(messages)
    messages.append(response)
    while messages[-1].has_tool_request:
        yield response.has_tool_request
        tool_result = invoke_tool(messages[-1].tool_request)
        yield tool_result
        messages.append({"tool_result": tool_result})
        response = llm(messages)
    yield response.text

However, a truer definition would be:
It is a builder pattern instantiating the loop defined above:
    - the message list has a builder pattern (compaction, system prompt, tool list, AGENT.md, SOUL.md, rules.MD, runaway loop prevention, memory providers)
    - the llm constructor has a builder pattern (various models, various system parameters, dynamic model choice depending on the task)
    - a list of skills is built
    - some default tools are provided (git worktree isolation, sandboxed code execution, browser use, computer_use, edit_file/read_file/bash/grep, TODO list, ask_user_questions)
    - the list of tools is concatenated with the MCP tools
    - the tool list needs to be able to invoke the tools
    - permissions for LLM use (token allocation) must be checked

Additionally, the result is usually structured:
    - plan-implement-verify loops
    - orchestrator loops
    - loops made from tool calls

Additionally, there is a plugin pattern:
    - model providers
    - image gen providers
    - gateway providers (for the gateway)
    - observability provider
    - security provider (guardrails, sandboxing, root_dir limitation)
    - voice / visions

Additionally, there is a hook pattern:
    - any event in the loop can be preempted, replaced, change the message list
    - works with guardrails
    - observability hooks
    - token permission/counting

Additionally, this is all wrapped in a robust threading framework:
    - try/retry
    - workflow durability
    - async for streaming results

Location:
    - Hermes:
        - default tools: /tools/
        - default skills: /skills/ and /optional-skills/
        - browser user: /plugins/browser/
        - context compaction: /plugins/context_engine/ 
        - image gen: /plugins/image_gen/
        - memory: /plugins/memory
        - LLM models: /plugins/model-providers
        - observability: /plugins/observability/
        - gateway chat provider: /plugins/platforms/
        - main agent code: /agent/
            - /agent/conversation_loop.py: main loop
            - /agent/\*_registry.py and /agent/\*_provider.py: for the above plugins
    - Gemini CLI:
        - /gemini-cli/packages/core/src/ the agentic core loop, organised in neat folders
        - does not contain lots of third party extensions, since this is Google software
    - OpenClaw:
        - all the extensions (gateway chat, models, image generation, memory implementation, voice provider, img and video generation): all in /extensions/
        - the core agentic code: /src/agents/ including sub directories for planning structures
        - extension registry: /src/, /src/memory and /src/context_engine/ in particular
        - tools and skills: /src/skills/ and /src/tools/





Typical sub components:
