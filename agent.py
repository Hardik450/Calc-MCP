import asyncio
import json
import os
from pathlib import Path
import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_DIR = Path(__file__).resolve().parent
MODEL = "qwen3.5:2b"
MAX_TOOL_ROUNDS = 8

def convert_mcp_tools(mcp_tools):
    "Convert MCP tools to Ollama tools format."
    ollama_tools = []
    for tool in mcp_tools:
        ollama_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        })
    return ollama_tools

def extract_tool_result(result) -> str:
    """Convert an MCP result into text for the model."""
    parts = []

    for block in result.content:
        text = getattr(block, "text", None)

        if text is not None:
            parts.append(text)
        else:
            parts.append(str(block))

    output = "\n".join(parts) or "Tool returned no text."

    if getattr(result, "isError", False):
        return f"Tool error: {output}"

    return output


async def main():
    client = ollama.AsyncClient()

    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "--directory",
            str(PROJECT_DIR),
            "python",
            "calc.py",
        ],
    )

    print("Starting Calculator MCP server...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            response = await session.list_tools()
            available_tools = {
                tool.name: tool for tool in response.tools
            }
            ollama_tools = convert_mcp_tools(response.tools)

            print("\nConnected to Calculator MCP server.")
            print("Available tools:", ", ".join(available_tools))
            print(f"Local model: {MODEL}")
            print("Type 'exit' to quit.\n")

            messages = [{
                "role": "system",
                "content": (
                    "You are a helpful calculator assistant. "
                    "Use the provided calculator tools for arithmetic. "
                    "For multi-step calculations, call tools as needed "
                    "and use their actual results. Explain the result "
                    "clearly. Never invent a tool result."
                ),
            }]

            while True:
                question = input("You: ").strip()

                if question.lower() in {"exit", "quit"}:
                    print("Goodbye!")
                    break

                if not question:
                    continue

                messages.append({
                    "role": "user",
                    "content": question,
                })

                for _ in range(MAX_TOOL_ROUNDS):
                    response = await client.chat(
                        model=MODEL,
                        messages=messages,
                        tools=ollama_tools,
                    )

                    message = response.message

                    messages.append(message)

                    if not message.tool_calls:
                        print(f"\nAssistant: {message.content}\n")
                        break

                    for tool_call in message.tool_calls:
                        name = tool_call.function.name
                        arguments = tool_call.function.arguments

                        print(f"[Calling tool: {name}]")

                        if name not in available_tools:
                            output = "Error: Unknown tool."
                        else:
                            try:
                                result = await session.call_tool(
                                    name,
                                    arguments=arguments,
                                )
                                output = extract_tool_result(result)
                            except Exception as exc:
                                output = (
                                    f"Tool execution failed: "
                                    f"{type(exc).__name__}: {exc}"
                                )

                        messages.append({
                            "role": "tool",
                            "tool_name": name,
                            "content": output,
                        })

                else:
                    print(
                        "\nStopped after the maximum tool-call rounds. "
                        "Try a simpler question.\n"
                    )

                if len(messages) > 25:
                    messages = [messages[0]] + messages[-20:]


if __name__ == "__main__":
    if os.name == "nt":
        os.system("chcp 65001 > nul")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
