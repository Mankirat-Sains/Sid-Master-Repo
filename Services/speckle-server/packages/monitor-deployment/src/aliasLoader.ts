import generateAliasesResolver from 'esm-module-alias'
import { srcRoot } from './root.js'
import path from 'node:path'
import { pathToFileURL } from 'url'

// esm-module-alias has bugs with Windows absolute paths
// Use pathToFileURL but extract pathname (not href) to avoid file:// prefix
const absoluteSrcRoot = path.resolve(srcRoot)
let normalizedSrcRoot = pathToFileURL(absoluteSrcRoot).pathname

// Remove leading slash for Windows paths (C:/Users/... not /C:/Users/...)
if (
  process.platform === 'win32' &&
  normalizedSrcRoot.startsWith('/') &&
  normalizedSrcRoot.length > 1 &&
  normalizedSrcRoot[2] === ':'
) {
  normalizedSrcRoot = normalizedSrcRoot.substring(1)
}

export const resolve = generateAliasesResolver({
  '@': normalizedSrcRoot
})
