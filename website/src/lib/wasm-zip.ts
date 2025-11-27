import init, { ZipProcessor } from '../../wasm-parser/pkg/wasm_parser';

let wasmInitialized = false;

export async function ensureWasmInit() {
	if (!wasmInitialized) {
		console.log('Initializing WASM...');
		try {
			await init();
			wasmInitialized = true;
			console.log('WASM initialized successfully');
		} catch (error) {
			console.error('WASM initialization failed:', error);
			throw error;
		}
	}
}

export interface ExtractedFile {
	path: string;
	data: Uint8Array;
	filename: string;
}

export async function extractZip(zipData: Uint8Array): Promise<{
	isDocpack: boolean;
	files: ExtractedFile[];
}> {
	await ensureWasmInit();

	const processor = new ZipProcessor();
	let isDocpack: boolean;
	try {
		isDocpack = processor.extract_zip(zipData);
	} catch (error) {
		console.error('WASM extract_zip error:', error);
		throw new Error(`Failed to extract zip: ${error}`);
	}
	
	let files: ExtractedFile[];
	try {
		files = processor.get_files() as ExtractedFile[];
	} catch (error) {
		console.error('WASM get_files error:', error);
		throw new Error(`Failed to get files: ${error}`);
	}

	return { isDocpack, files };
}

export async function extractZipToMap(zipData: Uint8Array): Promise<{
	isDocpack: boolean;
	filesMap: Map<string, File>;
}> {
	const { isDocpack, files } = await extractZip(zipData);
	const filesMap = new Map<string, File>();

	for (const extracted of files) {
		const file = new File([extracted.data], extracted.filename);
		filesMap.set(extracted.path, file);
	}

	return { isDocpack, filesMap };
}
