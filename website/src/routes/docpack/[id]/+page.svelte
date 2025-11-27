<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';

	interface FileNode {
		name: string;
		path: string;
		type: 'file' | 'directory';
		children?: FileNode[];
	}

	interface OutputFile {
		name: string;
		path: string;
		size: number;
	}

	interface DocpackData {
		manifest: {
			name: string;
			description: string;
			version: string;
			metadata: {
				created: string;
				language?: string;
			};
		};
		files: FileNode[];
		outputs: OutputFile[];
	}

	interface QueryResult {
		answer: string;
		sources: string[];
		thinking?: string;
	}

	let docpackId = $derived($page.params.id);
	let data = $state<DocpackData | null>(null);
	let loading = $state(true);
	let error = $state('');
	let selectedFile = $state<string | null>(null);
	let fileContent = $state('');
	let loadingContent = $state(false);
	let activeTab = $state<'files' | 'outputs'>('outputs');

	// Query Engine state
	let query = $state('');
	let queryResult = $state<QueryResult | null>(null);
	let queryLoading = $state(false);
	let queryError = $state('');

	onMount(async () => {
		await loadDocpack();
	});

	async function loadDocpack() {
		try {
			const response = await fetch(`/api/docpack/${docpackId}`);
			const result = await response.json();

			if (!response.ok) {
				throw new Error(result.error || 'Failed to load docpack');
			}

			data = result;
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			loading = false;
		}
	}

	async function loadFile(path: string) {
		selectedFile = path;
		loadingContent = true;
		fileContent = '';

		try {
			const response = await fetch(`/api/docpack/${docpackId}/file?path=${encodeURIComponent(path)}`);
			const result = await response.json();

			if (!response.ok) {
				throw new Error(result.error || 'Failed to load file');
			}

			fileContent = result.content;
		} catch (err) {
			fileContent = `Error loading file: ${err instanceof Error ? err.message : 'Unknown error'}`;
		} finally {
			loadingContent = false;
		}
	}

	async function submitQuery() {
		if (!query.trim()) return;

		queryLoading = true;
		queryError = '';
		queryResult = null;

		try {
			const response = await fetch(`/api/docpack/${docpackId}/query`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ query })
			});

			const result = await response.json();

			if (!response.ok) {
				throw new Error(result.error || 'Query failed');
			}

			queryResult = result;
		} catch (err) {
			queryError = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			queryLoading = false;
		}
	}

	function renderFileTree(nodes: FileNode[], level = 0): any {
		return nodes.map((node) => ({
			node,
			level,
			children: node.type === 'directory' && node.children ? renderFileTree(node.children, level + 1) : []
		}));
	}

	let flatTree = $derived(data ? renderFileTree(data.files).flat(Infinity) : []);
</script>

<div class="min-h-screen bg-linear-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
	<!-- Navigation -->
	<nav class="border-b border-slate-700">
		<div class="max-w-7xl mx-auto px-6 py-4">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-8">
					<a href="/" class="text-xl font-bold bg-linear-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
						Doctown
					</a>
					<a href="/commons" class="text-slate-400 hover:text-white transition-colors">
						The Commons
					</a>
				</div>
			</div>
		</div>
	</nav>

	<div class="max-w-7xl mx-auto px-6 py-8">
		{#if loading}
			<div class="flex items-center justify-center py-24">
				<div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-slate-600 border-t-blue-500"></div>
			</div>
		{:else if error}
			<div class="p-6 bg-red-500/10 border border-red-500 rounded-lg">
				<p class="text-red-400">{error}</p>
			</div>
		{:else if data}
			<!-- Header -->
			<div class="mb-8">
				<a href="/commons" class="text-sm text-slate-400 hover:text-slate-200 mb-4 inline-block">
					← Back to The Commons
				</a>
				<h1 class="text-4xl font-bold mb-2">{data.manifest.name}</h1>
				<p class="text-slate-400">{data.manifest.description}</p>
				<div class="flex gap-4 mt-4 text-sm text-slate-500">
					<span>Version {data.manifest.version}</span>
					<span>•</span>
					<span>Created {new Date(data.manifest.metadata.created).toLocaleString()}</span>
					{#if data.manifest.metadata.language}
						<span>•</span>
						<span>{data.manifest.metadata.language}</span>
					{/if}
				</div>
			</div>

			<!-- Query Engine -->
			<div class="mb-8">
				<div class="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
					<div class="flex items-center gap-3 mb-4">
						<div class="text-2xl">🔍</div>
						<h2 class="text-2xl font-bold">Query Engine</h2>
					</div>

					<form onsubmit={(e) => { e.preventDefault(); submitQuery(); }} class="mb-4">
						<div class="flex gap-3">
							<input
								type="text"
								bind:value={query}
								placeholder="Ask anything about this universe..."
								class="flex-1 px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
							/>
							<button
								type="submit"
								disabled={queryLoading || !query.trim()}
								class="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
							>
								{queryLoading ? 'Searching...' : 'Ask'}
							</button>
						</div>
					</form>

					{#if queryLoading}
						<div class="flex items-center gap-3 py-4 text-slate-400">
							<div class="inline-block animate-spin rounded-full h-5 w-5 border-2 border-slate-600 border-t-blue-500"></div>
							<span>AI agent is searching through your universe...</span>
						</div>
					{/if}

					{#if queryError}
						<div class="p-4 bg-red-500/10 border border-red-500 rounded-lg">
							<p class="text-red-400">{queryError}</p>
						</div>
					{/if}

					{#if queryResult}
						<div class="space-y-4">
							<div class="p-4 bg-slate-900/50 border border-slate-600 rounded-lg">
								<h3 class="text-sm font-semibold text-blue-400 mb-2">Answer</h3>
								<div class="text-slate-200 whitespace-pre-wrap">{queryResult.answer}</div>
							</div>

							{#if queryResult.sources && queryResult.sources.length > 0}
								<div class="p-4 bg-slate-900/50 border border-slate-600 rounded-lg">
									<h3 class="text-sm font-semibold text-slate-400 mb-2">Sources</h3>
									<div class="space-y-1">
										{#each queryResult.sources as source}
											<button
												onclick={() => loadFile(source)}
												class="text-sm text-blue-400 hover:text-blue-300 hover:underline block"
											>
												{source}
											</button>
										{/each}
									</div>
								</div>
							{/if}

							{#if queryResult.thinking}
								<details class="p-4 bg-slate-900/50 border border-slate-600 rounded-lg">
									<summary class="text-sm font-semibold text-slate-400 cursor-pointer">Chain of Thought</summary>
									<div class="mt-2 text-sm text-slate-500 whitespace-pre-wrap">{queryResult.thinking}</div>
								</details>
							{/if}
						</div>
					{/if}
				</div>
			</div>

			<!-- Tabs -->
			<div class="border-b border-slate-700 mb-6">
				<nav class="flex gap-8">
					<button
						class={`pb-3 px-1 border-b-2 font-medium transition-colors ${
							activeTab === 'outputs'
								? 'border-blue-500 text-blue-400'
								: 'border-transparent text-slate-400 hover:text-slate-200'
						}`}
						onclick={() => activeTab = 'outputs'}
					>
						Generated Documentation
					</button>
					<button
						class={`pb-3 px-1 border-b-2 font-medium transition-colors ${
							activeTab === 'files'
								? 'border-blue-500 text-blue-400'
								: 'border-transparent text-slate-400 hover:text-slate-200'
						}`}
						onclick={() => activeTab = 'files'}
					>
						Source Files
					</button>
				</nav>
			</div>

			<!-- Content -->
			<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
				<!-- File/Output List -->
				<div class="lg:col-span-1">
					<div class="bg-slate-800/50 border border-slate-700 rounded-lg p-4 max-h-[calc(100vh-24rem)] overflow-y-auto">
						{#if activeTab === 'outputs'}
							<h3 class="font-semibold mb-3">Output Files</h3>
							{#if data.outputs.length === 0}
								<p class="text-sm text-slate-500">No output files generated yet</p>
							{:else}
								<div class="space-y-1">
									{#each data.outputs as output}
										<button
											class={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
												selectedFile === `output/${output.name}`
													? 'bg-blue-600 text-white'
													: 'hover:bg-slate-700 text-slate-300'
											}`}
											onclick={() => loadFile(`output/${output.name}`)}
										>
											<div class="flex items-center gap-2">
												<span>📄</span>
												<span class="truncate">{output.name}</span>
											</div>
										</button>
									{/each}
								</div>
							{/if}
						{:else}
							<h3 class="font-semibold mb-3">Source Files</h3>
							<div class="space-y-1">
								{#each flatTree as { node, level }}
									<button
										class={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
											selectedFile === `files/${node.path}`
												? 'bg-blue-600 text-white'
												: 'hover:bg-slate-700 text-slate-300'
										}`}
										style={`padding-left: ${level * 12 + 12}px`}
										onclick={() => node.type === 'file' && loadFile(`files/${node.path}`)}
										disabled={node.type === 'directory'}
									>
										<div class="flex items-center gap-2">
											<span>{node.type === 'directory' ? '📁' : '📄'}</span>
											<span class="truncate">{node.name}</span>
										</div>
									</button>
								{/each}
							</div>
						{/if}
					</div>
				</div>

				<!-- File Viewer -->
				<div class="lg:col-span-2">
					<div class="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
						{#if !selectedFile}
							<div class="flex items-center justify-center h-[calc(100vh-24rem)] text-slate-500">
								Select a file to view
							</div>
						{:else if loadingContent}
							<div class="flex items-center justify-center h-[calc(100vh-24rem)]">
								<div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-slate-600 border-t-blue-500"></div>
							</div>
						{:else}
							<div class="p-6">
								<div class="mb-4 pb-4 border-b border-slate-700">
									<h3 class="font-mono text-sm text-slate-400">{selectedFile}</h3>
								</div>
								<div class="prose prose-invert prose-slate max-w-none">
									{#if selectedFile.endsWith('.md')}
										<div class="markdown-content">
											{@html fileContent}
										</div>
									{:else}
										<pre class="bg-slate-900 p-4 rounded overflow-x-auto"><code>{fileContent}</code></pre>
									{/if}
								</div>
							</div>
						{/if}
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.markdown-content {
		white-space: pre-wrap;
	}
</style>
