/**
 * Project number to Speckle model mapping
 * Similar to PROJECT_MODEL_MAP in Electron app
 */

import speckleMapping from '../../../Backend/references/speckle_mapping.json'

interface ProjectMapping {
  projectId: string;
  modelId: string;
  name: string;
  commitId?: string;
}

const PROJECT_MODEL_MAP: Record<string, ProjectMapping> = speckleMapping as Record<string, ProjectMapping>;

export const useProjectMapping = () => {
  function getProjectModelMapping(
    projectNumberOrName: string
  ): ProjectMapping | null {
    if (!projectNumberOrName) {
      return null;
    }
    return PROJECT_MODEL_MAP[projectNumberOrName] || null;
  }

  function getAllMappings(): Record<string, ProjectMapping> {
    return PROJECT_MODEL_MAP;
  }

  function findProjectByNumber(projectNumber: string): ProjectMapping | null {
    // Match format: XX-XX-XXX
    const normalized = projectNumber.trim();
    return PROJECT_MODEL_MAP[normalized] || null;
  }

  function findProjectByName(name: string): ProjectMapping | null {
    const normalized = name.trim();
    return PROJECT_MODEL_MAP[normalized] || null;
  }

  return {
    getProjectModelMapping,
    getAllMappings,
    findProjectByNumber,
    findProjectByName,
  };
};
