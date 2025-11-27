<script lang="ts">
	import { goto } from '$app/navigation';
	import JSZip from 'jszip';

	interface StagedDocpack {
		name: string;
		description: string;
		files: Map<string, File>;
		manifest: any;
		tasks: any;
	}

	let isDragging = $state(false);
	let stagedDocpack = $state<StagedDocpack | null>(null);
	let processing = $state(false);
	let error = $state('');

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		isDragging = true;
	}

	function handleDragLeave(e: DragEvent) {
		e.preventDefault();
		isDragging = false;
	}

	async function handleDrop(e: DragEvent) {
		e.preventDefault();
		isDragging = false;

		const items = e.dataTransfer?.items;
		if (!items) return;

		const files: File[] = [];
		for (let i = 0; i < items.length; i++) {
			const item = items[i];
			if (item.kind === 'file') {
				const file = item.getAsFile();
				if (file) files.push(file);
			}
		}

		if (files.length === 0) return;

		// Check if it's a .docpack file
		const docpackFile = files.find(f => f.name.endsWith('.docpack') || f.name.endsWith('.zip'));

		if (docpackFile && (docpackFile.name.endsWith('.docpack') || files.length === 1)) {
			await loadDocpack(docpackFile);
		} else if (stagedDocpack) {
			// Append files to staged docpack
			await appendFiles(files);
		} else {
			// Create new docpack from files
			await createDocpackFromFiles(files);
		}
	}

	async function handleFileInput(e: Event) {
		const input = e.target as HTMLInputElement;
		const files = Array.from(input.files || []);
		if (files.length === 0) return;

		if (files[0].name.endsWith('.docpack') || files[0].name.endsWith('.zip')) {
			await loadDocpack(files[0]);
		} else if (stagedDocpack) {
			await appendFiles(files);
		} else {
			await createDocpackFromFiles(files);
		}
	}

	async function loadDocpack(file: File) {
		try {
			error = '';
			const zip = await JSZip.loadAsync(file);

			// Read manifest
			const manifestFile = zip.file('docpack.json');
			if (!manifestFile) {
				throw new Error('Invalid docpack: missing docpack.json');
			}
			const manifestText = await manifestFile.async('text');
			const manifest = JSON.parse(manifestText);

			// Read tasks
			const tasksFile = zip.file('tasks.json');
			const tasks = tasksFile ? JSON.parse(await tasksFile.async('text')) : null;

			// Extract files
			const filesMap = new Map<string, File>();
			const filesFolder = zip.folder('files');

			if (filesFolder) {
				for (const [path, zipEntry] of Object.entries(zip.files)) {
					if (path.startsWith('files/') && !zipEntry.dir) {
						const blob = await zipEntry.async('blob');
						const fileName = path.replace('files/', '');
						filesMap.set(fileName, new File([blob], fileName));
					}
				}
			}

			stagedDocpack = {
				name: manifest.name || file.name.replace('.docpack', ''),
				description: manifest.description || '',
				files: filesMap,
				manifest,
				tasks
			};

		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load docpack';
		}
	}

	async function createDocpackFromFiles(files: File[]) {
		const filesMap = new Map<string, File>();
		files.forEach(file => filesMap.set(file.name, file));

		stagedDocpack = {
			name: files.length === 1 ? files[0].name : 'New Docpack',
			description: `Created from ${files.length} file${files.length > 1 ? 's' : ''}`,
			files: filesMap,
			manifest: {
				version: '1.0',
				name: files.length === 1 ? files[0].name : 'New Docpack',
				description: `Created from ${files.length} file${files.length > 1 ? 's' : ''}`,
				environment: {
					tools: ['list_files', 'read_file', 'write_output'],
					interpreter: 'python3.12',
					constraints: {
						max_file_reads: 1000,
						max_execution_time_seconds: 300,
						memory_limit_mb: 2048
					}
				},
				metadata: {
					created: new Date().toISOString(),
					creator: 'doctown-web',
					source_type: 'manual'
				}
			},
			tasks: {
				mission: 'Explore and document this content',
				tasks: [
					{
						id: 'task_1',
						name: 'Analyze content',
						description: 'Explore and create a comprehensive overview',
						tools_allowed: ['list_files', 'read_file', 'write_output'],
						output: {
							type: 'markdown',
							path: 'output/overview.md'
						}
					}
				],
				constraints: {
					chain_of_thought_location: '/workspace/.reasoning',
					forbidden_actions: ['modify_files', 'execute_code'],
					output_format: 'markdown'
				}
			}
		};
	}

	async function appendFiles(files: File[]) {
		if (!stagedDocpack) return;

		files.forEach(file => {
			stagedDocpack!.files.set(file.name, file);
		});

		stagedDocpack.description = `${stagedDocpack.files.size} file${stagedDocpack.files.size > 1 ? 's' : ''}`;
		stagedDocpack = stagedDocpack; // Trigger reactivity
	}

	async function finalizeDocpack() {
		if (!stagedDocpack) return;

		try {
			const zip = new JSZip();

			// Add manifest
			zip.file('docpack.json', JSON.stringify(stagedDocpack.manifest, null, 2));

			// Add tasks
			if (stagedDocpack.tasks) {
				zip.file('tasks.json', JSON.stringify(stagedDocpack.tasks, null, 2));
			}

			// Add files
			const filesFolder = zip.folder('files');
			if (filesFolder) {
				for (const [path, file] of stagedDocpack.files) {
					filesFolder.file(path, file);
				}
			}

			// Create empty output and index folders
			zip.folder('output');
			zip.folder('index');

			// Generate and download
			const blob = await zip.generateAsync({ type: 'blob' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `${stagedDocpack.name}.docpack`;
			a.click();
			URL.revokeObjectURL(url);

			// Clear staging
			stagedDocpack = null;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create docpack';
		}
	}

	async function processWithAI() {
		if (!stagedDocpack) return;

		processing = true;
		error = '';

		try {
			// First, create the docpack file
			const zip = new JSZip();
			zip.file('docpack.json', JSON.stringify(stagedDocpack.manifest, null, 2));
			if (stagedDocpack.tasks) {
				zip.file('tasks.json', JSON.stringify(stagedDocpack.tasks, null, 2));
			}
			const filesFolder = zip.folder('files');
			if (filesFolder) {
				for (const [path, file] of stagedDocpack.files) {
					filesFolder.file(path, file);
				}
			}
			zip.folder('output');
			zip.folder('index');

			const blob = await zip.generateAsync({ type: 'blob' });
			const file = new File([blob], `${stagedDocpack.name}.docpack`, { type: 'application/zip' });

			// Upload to server for processing
			const formData = new FormData();
			formData.append('file', file);

			const response = await fetch('/api/upload', {
				method: 'POST',
				body: formData
			});

			const result = await response.json();

			if (!response.ok) {
				throw new Error(result.error || 'Processing failed');
			}

			// Redirect to viewer
			goto(`/docpack/${result.docpackId}`);

		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
			processing = false;
		}
	}

	function clearStaging() {
		stagedDocpack = null;
		error = '';
	}
</script>

<div class="min-h-screen bg-[#f4f1e8] text-[#3a3a3a]" style="font-family: Georgia, 'Times New Roman', serif;">
	<!-- Navigation -->
	<nav class="border-b border-[#d4c9b0]" style="background: linear-gradient(to bottom, #faf8f3, #f4f1e8);">
		<div class="max-w-6xl mx-auto px-6 py-5">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-8">
					<a href="/" class="text-2xl" style="font-family: 'Courier New', monospace; color: #5a5a5a; font-weight: normal; letter-spacing: 0.05em;">
						doctown
					</a>
					<a href="/commons" class="text-[#7a7a7a] hover:text-[#3a3a3a] transition-colors underline decoration-dotted underline-offset-4" style="font-size: 0.95rem;">
						the commons
					</a>
				</div>
			</div>
		</div>
	</nav>

	<div class="max-w-5xl mx-auto px-6 py-16">
		<!-- Header -->
		<div class="mb-16">
			<h1 class="text-3xl mb-3" style="font-weight: normal; color: #4a4a4a; letter-spacing: 0.02em;">
				create your universe
			</h1>
			<p class="text-lg text-[#6a6a6a]" style="font-style: italic; font-weight: 300;">
				drag files, docpacks, or folders to build and explore
			</p>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
			<!-- Drop Zone -->
			<div>
				<h2 class="text-sm mb-4 tracking-wide uppercase text-[#8a8a8a]" style="font-family: 'Courier New', monospace; font-size: 0.7rem; letter-spacing: 0.15em;">Drop Zone</h2>
				<div
					class={`border-2 border-dashed rounded-sm p-12 text-center transition-all duration-300 min-h-[400px] flex items-center justify-center ${
						isDragging ? 'border-[#c9a86a] bg-[#faf6ed]' : 'border-[#d4c9b0] bg-white'
					}`}
					style="box-shadow: ${isDragging ? '0 2px 8px rgba(201, 168, 106, 0.15)' : '0 1px 3px rgba(0, 0, 0, 0.06)'};"
					ondragover={handleDragOver}
					ondragleave={handleDragLeave}
					ondrop={handleDrop}
					role="button"
					tabindex="0"
				>
					{#if processing}
						<div class="space-y-5">
							<div class="inline-block animate-spin rounded-full h-12 w-12 border-2 border-[#e0d5c0] border-t-[#c9a86a]"></div>
							<p class="text-base text-[#7a7a7a]" style="font-style: italic;">processing...</p>
						</div>
					{:else}
						<div class="space-y-6 w-full">
							<svg class="mx-auto h-14 w-14 text-[#b0a393]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
							</svg>

							<div>
								<p class="text-lg text-[#5a5a5a] mb-2" style="font-weight: 300;">
									{#if stagedDocpack}
										drop files to append
									{:else}
										drop files or a .docpack
									{/if}
								</p>
								<p class="text-[#8a8a8a] text-sm" style="font-style: italic;">
									individual files, folders, or .docpack archives
								</p>
							</div>

							<label class="inline-block">
								<input
									type="file"
									multiple
									class="hidden"
									onchange={handleFileInput}
								/>
								<span class="cursor-pointer inline-flex items-center px-5 py-2 bg-[#e8dcc8] hover:bg-[#d9c9ad] text-[#4a4a4a] rounded-sm transition-all duration-200 border border-[#d4c9b0]" style="font-size: 0.9rem; letter-spacing: 0.02em;">
									choose files
								</span>
							</label>
						</div>
					{/if}
				</div>

				{#if error}
					<div class="mt-5 p-4 bg-[#fef5f0] border border-[#d9a88a] rounded-sm">
						<p class="text-[#a0604a]" style="font-style: italic; font-size: 0.9rem;">{error}</p>
					</div>
				{/if}
			</div>

			<!-- Staging Area -->
			<div>
				<h2 class="text-sm mb-4 tracking-wide uppercase text-[#8a8a8a]" style="font-family: 'Courier New', monospace; font-size: 0.7rem; letter-spacing: 0.15em;">Staging Area</h2>
				<div class="border border-[#d4c9b0] rounded-sm p-6 bg-white min-h-[400px]" style="box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);">
					{#if stagedDocpack}
						<div class="space-y-5">
							<div class="pb-5 border-b border-[#e0d5c0]">
								<h3 class="text-xl mb-2" style="font-weight: normal; color: #4a4a4a;">{stagedDocpack.name}</h3>
								<p class="text-sm text-[#7a7a7a]" style="font-style: italic;">{stagedDocpack.description}</p>
							</div>

							<div>
								<h4 class="text-xs mb-3 uppercase tracking-wide text-[#8a8a8a]" style="font-family: 'Courier New', monospace; letter-spacing: 0.1em;">Contents</h4>
								<div class="space-y-1 max-h-48 overflow-y-auto">
									{#each Array.from(stagedDocpack.files.entries()) as [path, file]}
										<div class="flex items-center gap-2 text-sm py-1.5 px-2 hover:bg-[#faf8f3] transition-colors">
											<span class="text-[#b0a393]">•</span>
											<span class="truncate flex-1" style="font-family: 'Courier New', monospace; font-size: 0.85rem; color: #5a5a5a;">{path}</span>
											<span class="text-xs text-[#9a9a9a]">{(file.size / 1024).toFixed(1)}kb</span>
										</div>
									{/each}
								</div>
							</div>

							<div class="pt-5 border-t border-[#e0d5c0] space-y-2.5">
								<button
									onclick={finalizeDocpack}
									class="w-full px-4 py-2.5 bg-[#d4c9b0] hover:bg-[#c9b89a] text-[#3a3a3a] rounded-sm transition-all duration-200 border border-[#c0b5a0]"
									style="font-size: 0.9rem; letter-spacing: 0.02em;"
								>
									finalize & download
								</button>

								<button
									onclick={processWithAI}
									class="w-full px-4 py-2.5 bg-[#e8dcc8] hover:bg-[#d9c9ad] text-[#3a3a3a] rounded-sm transition-all duration-200 border border-[#d4c9b0]"
									style="font-size: 0.9rem; letter-spacing: 0.02em;"
								>
									process with ai
								</button>

								<button
									onclick={clearStaging}
									class="w-full px-4 py-2 bg-transparent hover:bg-[#faf8f3] text-[#7a7a7a] rounded-sm transition-all duration-200 border border-[#d4c9b0]"
									style="font-size: 0.85rem;"
								>
									clear
								</button>
							</div>
						</div>
					{:else}
						<div class="flex items-center justify-center h-full text-center">
							<div class="space-y-4">
								<div class="text-4xl opacity-30">∅</div>
								<p class="text-[#8a8a8a]" style="font-style: italic;">no docpack staged</p>
								<p class="text-sm text-[#9a9a9a]">drop files to begin</p>
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Info Cards -->
		<div class="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
			<div class="p-6 bg-white rounded-sm border border-[#d4c9b0]" style="box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);">
				<div class="text-2xl mb-3 opacity-60">◆</div>
				<h3 class="mb-2" style="font-weight: normal; color: #4a4a4a;">stage & build</h3>
				<p class="text-sm text-[#7a7a7a]" style="line-height: 1.6;">
					drop a .docpack to stage it, then append files or merge with others
				</p>
			</div>

			<div class="p-6 bg-white rounded-sm border border-[#d4c9b0]" style="box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);">
				<div class="text-2xl mb-3 opacity-60">◇</div>
				<h3 class="mb-2" style="font-weight: normal; color: #4a4a4a;">download locally</h3>
				<p class="text-sm text-[#7a7a7a]" style="line-height: 1.6;">
					finalize to download your .docpack file—no cloud required
				</p>
			</div>

			<div class="p-6 bg-white rounded-sm border border-[#d4c9b0]" style="box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);">
				<div class="text-2xl mb-3 opacity-60">◊</div>
				<h3 class="mb-2" style="font-weight: normal; color: #4a4a4a;">optional ai</h3>
				<p class="text-sm text-[#7a7a7a]" style="line-height: 1.6;">
					process with ai to generate documentation automatically
				</p>
			</div>
		</div>
	</div>
</div>
