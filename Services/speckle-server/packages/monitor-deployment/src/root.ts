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
