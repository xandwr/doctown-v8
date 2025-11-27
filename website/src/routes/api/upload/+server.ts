import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { spawn } from 'child_process';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { homedir } from 'os';
import { randomBytes } from 'crypto';

const TEMP_DIR = join(homedir(), '.localdoc', 'temp');
const OUTPUT_DIR = join(homedir(), '.localdoc', 'outputs');

export const POST: RequestHandler = async ({ request }) => {
	try {
		const formData = await request.formData();
		const file = formData.get('file') as File;

		if (!file) {
			return json({ error: 'No file uploaded' }, { status: 400 });
		}

		if (!file.name.endsWith('.zip')) {
			return json({ error: 'Only .zip files are allowed' }, { status: 400 });
		}

		// Create temp and output directories
		await mkdir(TEMP_DIR, { recursive: true });
		await mkdir(OUTPUT_DIR, { recursive: true });

		// Generate unique ID for this upload
		const docpackId = randomBytes(8).toString('hex');
		const timestamp = Date.now();
		const uploadName = file.name.replace('.zip', '');

		// Save uploaded file
		const zipPath = join(TEMP_DIR, `${docpackId}.zip`);
		const buffer = await file.arrayBuffer();
		await writeFile(zipPath, Buffer.from(buffer));

		// Extract zip to temp directory
		const extractPath = join(TEMP_DIR, docpackId);
		await mkdir(extractPath, { recursive: true });

		// Unzip using system unzip command
		await new Promise((resolve, reject) => {
			const unzip = spawn('unzip', ['-q', zipPath, '-d', extractPath]);
			unzip.on('close', (code) => {
				if (code === 0) resolve(null);
				else reject(new Error(`Unzip failed with code ${code}`));
			});
			unzip.on('error', reject);
		});

		// Create docpack using localdoc CLI
		const docpackPath = join(OUTPUT_DIR, `${uploadName}-${docpackId}.docpack`);
		const cliPath = join(process.cwd(), '..', 'cli');

		await new Promise((resolve, reject) => {
			const ingest = spawn(
				'cargo',
				['run', '--', 'ingest', extractPath, '--out', docpackPath, '--name', uploadName],
				{ cwd: cliPath }
			);

			let stderr = '';
			ingest.stderr?.on('data', (data) => {
				stderr += data.toString();
			});

			ingest.on('close', (code) => {
				if (code === 0) resolve(null);
				else reject(new Error(`Ingest failed: ${stderr}`));
			});
			ingest.on('error', reject);
		});

		// Run the documenter agent
		const envPath = join(process.cwd(), '..', '.env');
		await new Promise((resolve, reject) => {
			const run = spawn(
				'cargo',
				['run', '--', 'run', docpackPath, '--image', 'doctown:latest'],
				{
					cwd: cliPath,
					env: { ...process.env, ENV_FILE: envPath }
				}
			);

			let stdout = '';
			let stderr = '';

			run.stdout?.on('data', (data) => {
				stdout += data.toString();
				console.log('[documenter]', data.toString());
			});

			run.stderr?.on('data', (data) => {
				stderr += data.toString();
				console.error('[documenter]', data.toString());
			});

			run.on('close', (code) => {
				if (code === 0) resolve(null);
				else reject(new Error(`Documenter failed: ${stderr}`));
			});
			run.on('error', reject);
		});

		// Return the docpack ID
		return json({
			success: true,
			docpackId: `${uploadName}-${docpackId}`,
			message: 'Documentation generated successfully'
		});

	} catch (error) {
		console.error('Upload error:', error);
		return json(
			{ error: error instanceof Error ? error.message : 'Unknown error occurred' },
			{ status: 500 }
		);
	}
};
