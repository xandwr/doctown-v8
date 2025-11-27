import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { readdir, stat, readFile } from 'fs/promises';
import { join } from 'path';
import { homedir } from 'os';

const OUTPUT_DIR = join(homedir(), '.localdoc', 'outputs');

export const GET: RequestHandler = async () => {
	try {
		// Read all docpacks from output directory
		let files: string[];
		try {
			files = await readdir(OUTPUT_DIR);
		} catch {
			// Directory doesn't exist yet
			return json({ docpacks: [] });
		}

		const docpackDirs = files.filter((f) => f.endsWith('.docpack'));

		const docpacks = await Promise.all(
			docpackDirs.map(async (dir) => {
				const docpackPath = join(OUTPUT_DIR, dir);
				const manifestPath = join(docpackPath, 'docpack.json');

				try {
					const manifestData = await readFile(manifestPath, 'utf-8');
					const manifest = JSON.parse(manifestData);
					const stats = await stat(docpackPath);

					// Count files
					const filesDir = join(docpackPath, 'files');
					let fileCount = 0;
					try {
						const countFiles = async (dir: string): Promise<number> => {
							let count = 0;
							const items = await readdir(dir, { withFileTypes: true });
							for (const item of items) {
								if (item.isDirectory()) {
									count += await countFiles(join(dir, item.name));
								} else {
									count++;
								}
							}
							return count;
						};
						fileCount = await countFiles(filesDir);
					} catch {
						fileCount = 0;
					}

					// Calculate size
					const getDirSize = async (dir: string): Promise<number> => {
						let size = 0;
						try {
							const items = await readdir(dir, { withFileTypes: true });
							for (const item of items) {
								const itemPath = join(dir, item.name);
								if (item.isDirectory()) {
									size += await getDirSize(itemPath);
								} else {
									const stats = await stat(itemPath);
									size += stats.size;
								}
							}
						} catch {
							// Ignore errors
						}
						return size;
					};

					const totalSize = await getDirSize(docpackPath);
					const formatSize = (bytes: number): string => {
						if (bytes < 1024) return `${bytes} B`;
						if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
						return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
					};

					return {
						id: dir.replace('.docpack', ''),
						name: manifest.name || 'Untitled',
						description: manifest.description || 'No description',
						created: new Date(manifest.metadata?.created || stats.mtime).toLocaleDateString(),
						fileCount,
						size: formatSize(totalSize)
					};
				} catch (err) {
					console.error(`Error reading docpack ${dir}:`, err);
					return null;
				}
			})
		);

		// Filter out any failed reads and sort by date
		const validDocpacks = docpacks.filter((d) => d !== null).reverse();

		return json({ docpacks: validDocpacks });
	} catch (error) {
		console.error('Error listing docpacks:', error);
		return json(
			{ error: error instanceof Error ? error.message : 'Failed to list docpacks' },
			{ status: 500 }
		);
	}
};
