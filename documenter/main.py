"""
Doctown Agent Orchestrator
Runs an AI agent within a .docpack sandbox to complete documentation tasks.
"""
from openai import OpenAI
import json
import os
import sys
from sandbox import Sandbox
from tools import DocpackTools


def main():
    """Main orchestrator loop."""
    # Initialize sandbox (reads from /workspace in Docker)
    try:
        sandbox = Sandbox()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize tools
    tools = DocpackTools(sandbox)

    # Get AI client - support both OpenAI and Ollama
    use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
    
    if use_ollama:
        # Use Ollama (local or RunPod)
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434/v1")
        model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        client = OpenAI(
            base_url=ollama_base_url,
            api_key="ollama"  # Ollama doesn't need a real key
        )
        print(f"Using Ollama at {ollama_base_url} with model {model}")
    else:
        # Use OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
            print("Tip: Set USE_OLLAMA=true to use Ollama instead", file=sys.stderr)
            sys.exit(1)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        client = OpenAI(api_key=api_key)
        print(f"Using OpenAI with model {model}")

    # Load tasks from docpack
    tasks_config = sandbox.load_tasks()
    if tasks_config is None:
        print("Warning: No tasks.json found. Running in exploration mode.")
        tasks_config = {
            "mission": "Explore and understand the project structure",
            "tasks": []
        }

    # Get tool definitions based on manifest
    tool_definitions = tools.get_tool_definitions()

    print(f"Docpack: {sandbox.manifest.get('name', 'unknown')}")
    print(f"Mission: {tasks_config.get('mission')}")
    print(f"Tools enabled: {len(tool_definitions)}")
    print("-" * 60)

    # Build initial prompt from tasks
    if tasks_config.get("tasks"):
        task_descriptions = "\n".join([
            f"{i+1}. {task['name']}: {task['description']}"
            for i, task in enumerate(tasks_config["tasks"])
        ])
        initial_prompt = f"""You are a documentation agent working within a .docpack environment.

Your mission: {tasks_config['mission']}

Tasks to complete:
{task_descriptions}

Begin by exploring the project structure and then complete each task in order.
Use the available tools to read files, search code, and query the semantic graph.
Write your outputs using the write_output tool as specified in each task.
"""
    else:
        # Fallback exploration mode
        initial_prompt = f"""You are a documentation agent working within a .docpack environment.

Your mission: {tasks_config['mission']}

Explore the project at '.' and provide a comprehensive summary of its structure and purpose.
"""

    # Initialize conversation
    messages = [{"role": "user", "content": initial_prompt}]

    # Agent loop (max iterations to prevent infinite loops)
    max_iterations = 20
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"\n[Iteration {iteration}]")

        # Call the agent
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_definitions,
            tool_choice="auto"
        )

        message = response.choices[0].message
        messages.append(message)

        # Check if agent wants to use tools
        if message.tool_calls:
            print(f"Agent calling {len(message.tool_calls)} tool(s)...")

            # Process each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                print(f"  - {tool_name}({', '.join(f'{k}={v}' for k, v in args.items())})")

                # Execute the tool
                result = tools.execute(tool_name, args)

                # Special handling for read_image and read_pdf - convert to vision format
                if tool_name in ("read_image", "read_pdf") and "base64" in result:
                    page_info = f" (page {result['page']})" if "page" in result else ""
                    file_desc = result.get('format', 'Image')
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps({
                            "success": True,
                            "message": f"{file_desc} loaded: {result['path']}{page_info}. You can now analyze it in your response."
                        })
                    })
                    # Add image as a follow-up user message for vision analysis
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Analyze this image from {result['path']}{page_info}:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{result['mime_type']};base64,{result['base64']}"
                                }
                            }
                        ]
                    })
                else:
                    # Standard tool result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps(result)
                    })

        # Check if agent is done (no more tool calls and has content)
        elif message.content:
            print("\n" + "=" * 60)
            print("AGENT FINAL RESPONSE:")
            print("=" * 60)
            print(message.content)
            print("=" * 60)
            break

        else:
            print("Agent finished without output.")
            break

    if iteration >= max_iterations:
        print(f"\nWarning: Reached maximum iterations ({max_iterations})")

    print(f"\nCompleted in {iteration} iterations.")
    print(f"Output directory: {sandbox.output_dir}")


if __name__ == "__main__":
    main()