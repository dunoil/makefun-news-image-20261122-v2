// Sunday 22 November 2026 world news broadsheet (Node 22, standard library only).
// The entry image is rendered by render.py and shipped beside this file;
// this program copies it to /output/entry.png. The gate takes a whole PNG
// of at most 1 MiB and 1024 by 1024 pixels, and the judge sees exactly
// the bytes copied.
//
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, mkdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outDir, { recursive: true });

// Self-check: the shipped image must be a whole PNG inside the gate limits
// (at most 1 MiB, at most 1024 by 1024) before it is copied anywhere.
const src = new URL('./entry.png', import.meta.url);
const bytes = readFileSync(src);
const pngMagic = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
if (!bytes.subarray(0, 8).equals(pngMagic)) {
  throw new Error('entry.png is not a PNG');
}
if (bytes.length > 1048576) {
  throw new Error(`entry.png is ${bytes.length} bytes, over the 1 MiB gate`);
}
const width = bytes.readUInt32BE(16);
const height = bytes.readUInt32BE(20);
if (width > 1024 || height > 1024) {
  throw new Error(`entry.png is ${width}x${height}, over the 1024px gate`);
}
if (statSync(src).size < 400000) {
  throw new Error('entry.png is under 400 KB, below the planned size floor');
}
copyFileSync(src, join(outDir, 'entry.png'));
