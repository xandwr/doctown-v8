import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { readdir, readFile, stat } from 'fs/promises';
import { join } from 'path';
import { homedir } from 'os';

const OUTPUT_DIR = join(homedir(), '.localdoc', 'docpacks');

interface FileNode {
	name: string;
	path: string;
	type: 'file' | 'directory';
	children?: FileNode[];
}

async function buildFileTree(dir: string, basePath = ''): Promise<FileNode[]> {
	const items = await readdir(dir, { withFileTypes: true });
	const nodes: FileNode[] = [];

	for (const item of items) {
		const itemPath = join(dir, item.name);
		const relativePath = basePath ? `${basePath}/${item.name}` : item.name;

		if (item.isDirectory()) {
			const children = await buildFileTree(itemPath, relativePath);
			nodes.push({
				name: item.name,
				path: relativePath,
				type: 'directory',
				children
			});
		} else {
			nodes.push({
				name: item.name,
				path: relativePath,
				type: 'file'
			});
		}
	}

	return nodes.sort((a, b) => {
		if (a.type === b.type) return a.name.localeCompare(b.name);
		return a.type === 'directory' ? -1 : 1;
	});
}

export const GET: RequestHandler = async ({ params }) => {
	try {
		const docpackPath = join(OUTPUT_DIR, `${params.id}.docpack`);
		console.log('Loading docpack from:', docpackPath);

		// Check if docpack exists
		try {
			await stat(docpackPath);
		} catch (err) {
			console.error('Docpack not found:', docpackPath);
			return json({ error: `Docpack not found: ${params.id}` }, { status: 404 });
		}

		// Read manifest
		const manifestPath = join(docpackPath, 'docpack.json');
		const manifestData = await readFile(manifestPath, 'utf-8');
		const manifest = JSON.parse(manifestData);

		// Build file tree
		const filesDir = join(docpackPath, 'files');
		let files: FileNode[] = [];
		try {
			files = await buildFileTree(filesDir);
		} catch {
			files = [];
		}

		// List output files
		const outputDir = join(docpackPath, 'output');
		let outputs: { name: string; path: string; size: number }[] = [];
		try {
			const outputFiles = await readdir(outputDir);
			outputs = await Promise.all(
				outputFiles.map(async (file) => {
					const filePath = join(outputDir, file);
					const stats = await stat(filePath);
					return {
						name: file,
						path: file,
						size: stats.size
					};
				})
			);
		} catch {
			outputs = [];
		}

		return json({
			manifest,
			files,
			outputs
		});
	} catch (error) {
		console.error('Error loading docpack:', error);
		return json(
			{ error: error instanceof Error ? error.message : 'Failed to load docpack' },
			{ status: 500 }
		);
	}
};
