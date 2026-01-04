import generateAliasesResolver from 'esm-module-alias'
import path from 'node:path'
import fs from 'node:fs'
import { fileURLToPath } from 'url'

/**
 * Singleton module for src root and package root directory resolution
 */
const __filename = fileURLToPath(import.meta.url)
// Ensure we get an absolute path
const srcRoot = path.resolve(path.dirname(__filename))

// Recursively walk back from __dirname till we find our package.json
let packageRoot = srcRoot
while (true) {
  const parentDir = path.resolve(packageRoot, '..')
  if (fs.readdirSync(packageRoot).includes('package.json')) {
    break
  }
  // Stop if we've reached the root (works for both Unix and Windows)
  if (parentDir === packageRoot) {
    break
  }
  packageRoot = parentDir
}

export { srcRoot, packageRoot }

// esm-module-alias has bugs with Windows absolute paths
// Convert to forward slashes and ensure it's normalized
let normalizedSrcRoot = path.resolve(srcRoot)
let normalizedTestsPath = path.resolve(packageRoot, './tests')

// On Windows, esm-module-alias expects forward slashes (POSIX-style)
if (process.platform === 'win32') {
  normalizedSrcRoot = normalizedSrcRoot.replace(/\\/g, '/')
  normalizedTestsPath = normalizedTestsPath.replace(/\\/g, '/')
  // Ensure paths start with / for proper absolute path format
  if (!normalizedSrcRoot.startsWith('/')) {
    normalizedSrcRoot = '/' + normalizedSrcRoot
  }
  if (!normalizedTestsPath.startsWith('/')) {
    normalizedTestsPath = '/' + normalizedTestsPath
  }
}

export const resolve = generateAliasesResolver({
  '@': normalizedSrcRoot,
  '#': normalizedTestsPath
})
