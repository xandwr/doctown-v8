import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { readFile } from 'fs/promises';
import { join } from 'path';
import { homedir } from 'os';

const OUTPUT_DIR = join(homedir(), '.localdoc', 'outputs');

export const GET: RequestHandler = async ({ params, url }) => {
	try {
		const filePath = url.searchParams.get('path');
		if (!filePath) {
			return json({ error: 'No file path provided' }, { status: 400 });
		}

		// Security: prevent directory traversal
		if (filePath.includes('..')) {
			return json({ error: 'Invalid file path' }, { status: 400 });
		}

		const docpackPath = join(OUTPUT_DIR, `${params.id}.docpack`);
		const fullPath = join(docpackPath, filePath);

		const content = await readFile(fullPath, 'utf-8');

		return json({ content });
	} catch (error) {
		console.error('Error reading file:', error);
		return json(
			{ error: error instanceof Error ? error.message : 'Failed to read file' },
			{ status: 500 }
		);
	}
};
