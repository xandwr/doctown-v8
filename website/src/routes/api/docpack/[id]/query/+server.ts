import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { spawn } from 'child_process';
import { join } from 'path';
import { homedir } from 'os';

const OUTPUT_DIR = join(homedir(), '.localdoc', 'outputs');

export const POST: RequestHandler = async ({ params, request }) => {
	try {
		const { query } = await request.json();

		if (!query || typeof query !== 'string') {
			return json({ error: 'Query is required' }, { status: 400 });
		}

		const docpackPath = join(OUTPUT_DIR, `${params.id}.docpack`);

		// Run a simplified AI agent that uses the same tools but focused on answering a query
		const envPath = join(process.cwd(), '..', '.env');

		return new Promise((resolve) => {
			const queryAgent = spawn(
				'docker',
				[
					'run',
					'--rm',
					'--env-file',
					envPath,
					'-v',
					`${docpackPath}:/workspace`,
					'-e',
					`QUERY=${query}`,
					'doctown:latest',
					'python',
					'-c',
					`
import os
import sys
import json
from openai import OpenAI
from sandbox import Sandbox
from tools import DocpackTools

# Initialize
sandbox = Sandbox()
tools = DocpackTools(sandbox)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
query = os.getenv("QUERY")

# Build query prompt
prompt = f"""You are a Query Engine for a .docpack universe. A user has asked:

"{query}"

Use the available tools to search through the files, read relevant content, and provide an accurate, detailed answer.

IMPORTANT:
- Use list_files to explore the structure
- Use read_file to read relevant files
- Search systematically and cite specific files/sections
- Provide a clear, direct answer
- List all source files you referenced

Your response should be structured as:
ANSWER: [your detailed answer here]
SOURCES: [list of file paths you referenced]
"""

messages = [{"role": "user", "content": prompt}]
tool_definitions = tools.get_tool_definitions()

# Query loop (max 15 iterations)
max_iterations = 15
iteration = 0
thinking_log = []

while iteration < max_iterations:
	iteration += 1

	response = client.chat.completions.create(
		model=5-nano",
		messages=messages,
		tools=tool_definitions,
		tool_choice="auto"
	)

	message = response.choices[0].message
	messages.append(message)

	# Track thinking
	if message.content:
		thinking_log.append(f"[Iteration {iteration}] {message.content[:200]}...")

	if message.tool_calls:
		for tool_call in message.tool_calls:
			tool_name = tool_call.function.name
			args = json.loads(tool_call.function.arguments)
			result = tools.execute(tool_name, args)

			thinking_log.append(f"[Tool] {tool_name}({args})")

			messages.append({
				"role": "tool",
				"tool_call_id": tool_call.id,
				"name": tool_name,
				"content": json.dumps(result)
			})
	elif message.content:
		# Agent has finished
		content = message.content

		# Parse answer and sources
		answer = content
		sources = []

		if "ANSWER:" in content:
			parts = content.split("SOURCES:")
			answer = parts[0].replace("ANSWER:", "").strip()
			if len(parts) > 1:
				source_text = parts[1].strip()
				sources = [s.strip() for s in source_text.split("\\n") if s.strip() and s.strip() != "-"]

		# Output JSON
		result = {
			"answer": answer,
			"sources": sources,
			"thinking": "\\n".join(thinking_log)
		}
		print(json.dumps(result))
		sys.exit(0)
	else:
		break

# Fallback
print(json.dumps({"answer": "Unable to find a complete answer", "sources": [], "thinking": "\\n".join(thinking_log)}))
`
				],
				{ env: { ...process.env } }
			);

			let stdout = '';
			let stderr = '';

			queryAgent.stdout?.on('data', (data) => {
				stdout += data.toString();
			});

			queryAgent.stderr?.on('data', (data) => {
				stderr += data.toString();
			});

			queryAgent.on('close', (code) => {
				if (code === 0 && stdout.trim()) {
					try {
						// Parse the last line of JSON output
						const lines = stdout.trim().split('\n');
						const lastLine = lines[lines.length - 1];
						const result = JSON.parse(lastLine);
						resolve(json(result));
					} catch (err) {
						console.error('Failed to parse query result:', err);
						resolve(json({ error: 'Failed to parse query result', raw: stdout }, { status: 500 }));
					}
				} else {
					resolve(json({ error: `Query failed: ${stderr}`, code }, { status: 500 }));
				}
			});

			queryAgent.on('error', (err) => {
				resolve(json({ error: err.message }, { status: 500 }));
			});
		});

	} catch (error) {
		console.error('Query error:', error);
		return json(
			{ error: error instanceof Error ? error.message : 'Failed to process query' },
			{ status: 500 }
		);
	}
};
