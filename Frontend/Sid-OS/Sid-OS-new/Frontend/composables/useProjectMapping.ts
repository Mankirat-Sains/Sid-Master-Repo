/**
 * Project number to Speckle model mapping
 * Similar to PROJECT_MODEL_MAP in Electron app
 */

interface ProjectMapping {
  projectId: string;
  modelId: string;
  name: string;
  commitId?: string;
}

const PROJECT_MODEL_MAP: Record<string, ProjectMapping> = {
  "25-08-127": {
    projectId: "b44d7945a3",
    modelId: "1711f08980",
    name: "Beef Barn Parlour Addition",
  },
  "Beef Barn Parlour Addition": {
    projectId: "b44d7945a3",
    modelId: "1711f08980",
    name: "Beef Barn Parlour Addition",
  },
  "25-07-066": {
    projectId: "b934667233",
    modelId: "7a94658d86",
    name: "Albers Layer Barn",
  },
  "Albers Layer Barn": {
    projectId: "b934667233",
    modelId: "7a94658d86",
    name: "Albers Layer Barn",
  },
};

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

