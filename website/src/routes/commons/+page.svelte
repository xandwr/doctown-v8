<script lang="ts">
	import { onMount } from 'svelte';

	interface Docpack {
		id: string;
		name: string;
		created: string;
		description: string;
		fileCount: number;
		size: string;
	}

	let docpacks = $state<Docpack[]>([]);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		try {
			const response = await fetch('/api/docpacks');
			const data = await response.json();

			if (!response.ok) {
				throw new Error(data.error || 'Failed to load docpacks');
			}

			docpacks = data.docpacks;
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			loading = false;
		}
	});
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
					<a href="/commons" class="text-white font-medium">
						The Commons
					</a>
				</div>
			</div>
		</div>
	</nav>

	<div class="max-w-6xl mx-auto px-6 py-16">
		<div class="flex items-center justify-between mb-12">
			<div>
				<h1 class="text-4xl font-bold mb-2">The Commons</h1>
				<p class="text-slate-400">Your collection of documented universes</p>
			</div>
			<a
				href="/"
				class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
			>
				Create New
			</a>
		</div>

		{#if loading}
			<div class="flex items-center justify-center py-24">
				<div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-slate-600 border-t-blue-500"></div>
			</div>
		{:else if error}
			<div class="p-6 bg-red-500/10 border border-red-500 rounded-lg">
				<p class="text-red-400">{error}</p>
			</div>
		{:else if docpacks.length === 0}
			<div class="text-center py-24">
				<div class="text-6xl mb-4">🌌</div>
				<h3 class="text-2xl font-semibold mb-2">The Commons awaits</h3>
				<p class="text-slate-400 mb-6">Create your first universe to populate The Commons</p>
				<a
					href="/"
					class="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
				>
					Create Your First Universe
				</a>
			</div>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
				{#each docpacks as docpack (docpack.id)}
					<a
						href="/docpack/{docpack.id}"
						class="block p-6 bg-slate-800/50 border border-slate-700 rounded-xl hover:border-blue-500 hover:bg-slate-800/70 transition-all group"
					>
						<div class="flex items-start justify-between mb-3">
							<div class="text-3xl">📦</div>
							<div class="text-xs text-slate-500">{docpack.created}</div>
						</div>

						<h3 class="text-xl font-semibold mb-2 group-hover:text-blue-400 transition-colors">
							{docpack.name}
						</h3>

						<p class="text-sm text-slate-400 mb-4">
							{docpack.description}
						</p>

						<div class="flex items-center gap-4 text-xs text-slate-500">
							<span>{docpack.fileCount} files</span>
							<span>•</span>
							<span>{docpack.size}</span>
						</div>
					</a>
				{/each}
			</div>
		{/if}
	</div>
</div>
