// Folder statistics synthetic data for project workspace dashboard

export interface ModificationLog {
  id: string
  timestamp: string
  user: string
  fileName: string
  action: 'created' | 'modified' | 'deleted'
  summary: string
  filesAffected: number
}

export interface TaskItem {
  id: string
  title: string
  description: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  status: 'not-started' | 'in-progress' | 'completed'
  estimatedHours: number
  dueDate: string
  assignee?: string
}

export interface TimeEntry {
  date: string
  hours: number
  user: string
  activity: string
}

export interface FileTypeDistribution {
  type: string
  count: number
  totalSize: number // in MB
}

export interface ProjectionData {
  week: number
  plannedCompletion: number
  actualCompletion: number
  projectedCompletion: number
}

export interface FolderStatistics {
  projectId: string
  projectName: string
  folderPath: string
  
  // File metrics
  totalFiles: number
  totalFolders: number
  totalSize: number // in MB
  fileTypes: FileTypeDistribution[]
  
  // Time tracking
  totalHours: number
  hoursThisWeek: number
  hoursThisMonth: number
  timeByUser: Array<{ user: string; hours: number }>
  timeByDay: TimeEntry[]
  
  // Tasks
  tasks: TaskItem[]
  completedTasks: number
  inProgressTasks: number
  notStartedTasks: number
  
  // Modifications
  recentModifications: ModificationLog[]
  modificationsThisWeek: number
  modificationsThisMonth: number
  
  // Projections
  completionPercentage: number
  projectedCompletionDate: string
  projectStatus: 'on-track' | 'at-risk' | 'behind' | 'ahead'
  weeklyProgress: ProjectionData[]
  
  // Activity heatmap (for visualization)
  activityByHour: Array<{ hour: number; activity: number }>
  activityByDay: Array<{ day: string; commits: number; hours: number }>
}

// Sample data for a project folder
export const sampleFolderStatistics: FolderStatistics = {
  projectId: '25-01-101',
  projectName: 'Mark Craig 60\' x 100\' Shed Addition',
  folderPath: '/Volumes/J/25-01-101',
  
  totalFiles: 247,
  totalFolders: 12,
  totalSize: 1847.5, // MB
  
  fileTypes: [
    { type: '.rvt', count: 8, totalSize: 1240.8 },
    { type: '.pdf', count: 42, totalSize: 385.2 },
    { type: '.dwg', count: 18, totalSize: 156.4 },
    { type: '.xlsx', count: 35, totalSize: 48.6 },
    { type: '.docx', count: 28, totalSize: 12.8 },
    { type: '.png', count: 89, totalSize: 2.4 },
    { type: '.txt', count: 15, totalSize: 0.8 },
    { type: 'other', count: 12, totalSize: 0.5 },
  ],
  
  totalHours: 127.5,
  hoursThisWeek: 18.5,
  hoursThisMonth: 84.2,
  
  timeByUser: [
    { user: 'James Hinsperger', hours: 68.5 },
    { user: 'Sarah Chen', hours: 32.0 },
    { user: 'Michael Rodriguez', hours: 18.5 },
    { user: 'Emily Watson', hours: 8.5 },
  ],
  
  timeByDay: [
    { date: '2026-01-08', hours: 6.5, user: 'James Hinsperger', activity: 'Beam design calculations' },
    { date: '2026-01-08', hours: 3.0, user: 'Sarah Chen', activity: 'Foundation review' },
    { date: '2026-01-09', hours: 8.0, user: 'James Hinsperger', activity: 'Revit modeling - structural framing' },
    { date: '2026-01-09', hours: 4.5, user: 'Michael Rodriguez', activity: 'Connection details' },
    { date: '2026-01-10', hours: 7.5, user: 'James Hinsperger', activity: 'Load calculations & code checks' },
    { date: '2026-01-10', hours: 2.5, user: 'Emily Watson', activity: 'Drawing annotations' },
    { date: '2026-01-13', hours: 5.5, user: 'James Hinsperger', activity: 'Structural analysis in RISA' },
    { date: '2026-01-13', hours: 4.0, user: 'Sarah Chen', activity: 'Design review meeting' },
    { date: '2026-01-14', hours: 8.5, user: 'James Hinsperger', activity: 'Final calculations & report' },
    { date: '2026-01-14', hours: 3.5, user: 'Michael Rodriguez', activity: 'Drawing production' },
  ],
  
  tasks: [
    {
      id: 'task-1',
      title: 'Complete foundation design calculations',
      description: 'Finalize spread footing design and pier foundation analysis. Include soil bearing pressure checks and settlement calculations.',
      priority: 'critical',
      status: 'in-progress',
      estimatedHours: 6.0,
      dueDate: '2026-01-16',
      assignee: 'James Hinsperger',
    },
    {
      id: 'task-2',
      title: 'Review and approve structural drawings',
      description: 'QA/QC review of all structural drawings including framing plans, foundation plans, and connection details.',
      priority: 'high',
      status: 'not-started',
      estimatedHours: 4.5,
      dueDate: '2026-01-17',
      assignee: 'Sarah Chen',
    },
    {
      id: 'task-3',
      title: 'Finalize beam and column schedules',
      description: 'Complete all member schedules with final sizes, verify against analysis results, and add to drawing set.',
      priority: 'high',
      status: 'in-progress',
      estimatedHours: 3.0,
      dueDate: '2026-01-16',
      assignee: 'James Hinsperger',
    },
    {
      id: 'task-4',
      title: 'Prepare structural calculation package',
      description: 'Compile all calculations into organized package for permit submission. Include load calculations, member design, and code references.',
      priority: 'critical',
      status: 'in-progress',
      estimatedHours: 8.0,
      dueDate: '2026-01-18',
      assignee: 'James Hinsperger',
    },
    {
      id: 'task-5',
      title: 'Update Revit model with final changes',
      description: 'Incorporate all design changes and annotations into the master Revit model.',
      priority: 'medium',
      status: 'completed',
      estimatedHours: 5.0,
      dueDate: '2026-01-14',
      assignee: 'Michael Rodriguez',
    },
    {
      id: 'task-6',
      title: 'Coordinate with architect on penetrations',
      description: 'Review architectural drawings and coordinate structural opening sizes and locations.',
      priority: 'medium',
      status: 'not-started',
      estimatedHours: 2.0,
      dueDate: '2026-01-17',
      assignee: 'Sarah Chen',
    },
    {
      id: 'task-7',
      title: 'Seismic design checks (OBC 2012)',
      description: 'Verify seismic load path and capacity design requirements per Ontario Building Code.',
      priority: 'high',
      status: 'completed',
      estimatedHours: 6.5,
      dueDate: '2026-01-13',
      assignee: 'James Hinsperger',
    },
    {
      id: 'task-8',
      title: 'Connection detail drawings',
      description: 'Create detailed connection drawings for beam-column connections, base plates, and moment connections.',
      priority: 'high',
      status: 'completed',
      estimatedHours: 7.0,
      dueDate: '2026-01-15',
      assignee: 'Michael Rodriguez',
    },
    {
      id: 'task-9',
      title: 'Wind load analysis',
      description: 'Complete wind load calculations per NBC 2020 for all structural elements.',
      priority: 'critical',
      status: 'completed',
      estimatedHours: 4.0,
      dueDate: '2026-01-12',
      assignee: 'James Hinsperger',
    },
    {
      id: 'task-10',
      title: 'Prepare submittal package',
      description: 'Compile all drawings, calculations, and specifications for building permit submission.',
      priority: 'critical',
      status: 'not-started',
      estimatedHours: 3.5,
      dueDate: '2026-01-20',
      assignee: 'Sarah Chen',
    },
  ],
  
  completedTasks: 4,
  inProgressTasks: 3,
  notStartedTasks: 3,
  
  recentModifications: [
    {
      id: 'mod-1',
      timestamp: '2026-01-14T16:42:00',
      user: 'James Hinsperger',
      fileName: 'Structural Calculations.xlsx',
      action: 'modified',
      summary: 'Updated beam deflection calculations for Grid B members',
      filesAffected: 1,
    },
    {
      id: 'mod-2',
      timestamp: '2026-01-14T14:28:00',
      user: 'Michael Rodriguez',
      fileName: 'S-201_Foundation_Plan.dwg',
      action: 'modified',
      summary: 'Added dimension strings and detail callouts',
      filesAffected: 1,
    },
    {
      id: 'mod-3',
      timestamp: '2026-01-14T11:15:00',
      user: 'James Hinsperger',
      fileName: 'Mark Craig Shed - Structural.rvt',
      action: 'modified',
      summary: 'Revised beam sizes on grid lines 2-4 per analysis',
      filesAffected: 1,
    },
    {
      id: 'mod-4',
      timestamp: '2026-01-13T16:55:00',
      user: 'Sarah Chen',
      fileName: 'Design Review Notes.docx',
      action: 'created',
      summary: 'Created design review meeting notes with action items',
      filesAffected: 1,
    },
    {
      id: 'mod-5',
      timestamp: '2026-01-13T15:20:00',
      user: 'James Hinsperger',
      fileName: 'RISA_Analysis_v3.r3d',
      action: 'modified',
      summary: 'Updated load combinations and ran final analysis',
      filesAffected: 1,
    },
    {
      id: 'mod-6',
      timestamp: '2026-01-13T10:05:00',
      user: 'Michael Rodriguez',
      fileName: 'Connection Details/',
      action: 'modified',
      summary: 'Updated 12 connection detail drawings with weld callouts',
      filesAffected: 12,
    },
    {
      id: 'mod-7',
      timestamp: '2026-01-10T14:32:00',
      user: 'Emily Watson',
      fileName: 'S-101_Framing_Plan.dwg',
      action: 'modified',
      summary: 'Added member size annotations and grid labels',
      filesAffected: 1,
    },
    {
      id: 'mod-8',
      timestamp: '2026-01-09T16:10:00',
      user: 'James Hinsperger',
      fileName: 'Load Calculations.pdf',
      action: 'created',
      summary: 'Generated PDF of dead, live, snow, and wind load calculations',
      filesAffected: 1,
    },
  ],
  
  modificationsThisWeek: 18,
  modificationsThisMonth: 76,
  
  completionPercentage: 78,
  projectedCompletionDate: '2026-01-20',
  projectStatus: 'on-track',
  
  weeklyProgress: [
    { week: 1, plannedCompletion: 15, actualCompletion: 12, projectedCompletion: 15 },
    { week: 2, plannedCompletion: 32, actualCompletion: 30, projectedCompletion: 32 },
    { week: 3, plannedCompletion: 50, actualCompletion: 48, projectedCompletion: 50 },
    { week: 4, plannedCompletion: 68, actualCompletion: 65, projectedCompletion: 68 },
    { week: 5, plannedCompletion: 85, actualCompletion: 78, projectedCompletion: 82 },
    { week: 6, plannedCompletion: 100, actualCompletion: 78, projectedCompletion: 95 },
  ],
  
  activityByHour: [
    { hour: 8, activity: 12 },
    { hour: 9, activity: 24 },
    { hour: 10, activity: 28 },
    { hour: 11, activity: 22 },
    { hour: 12, activity: 8 },
    { hour: 13, activity: 18 },
    { hour: 14, activity: 26 },
    { hour: 15, activity: 30 },
    { hour: 16, activity: 24 },
    { hour: 17, activity: 10 },
  ],
  
  activityByDay: [
    { day: 'Mon', commits: 8, hours: 7.5 },
    { day: 'Tue', commits: 12, hours: 9.5 },
    { day: 'Wed', commits: 15, hours: 8.0 },
    { day: 'Thu', commits: 11, hours: 10.5 },
    { day: 'Fri', commits: 9, hours: 8.5 },
    { day: 'Sat', commits: 2, hours: 2.5 },
    { day: 'Sun', commits: 0, hours: 0.0 },
  ],
}

export function getProjectStatus(percentage: number): FolderStatistics['projectStatus'] {
  if (percentage >= 95) return 'ahead'
  if (percentage >= 75) return 'on-track'
  if (percentage >= 60) return 'at-risk'
  return 'behind'
}

export function getPriorityColor(priority: TaskItem['priority']): string {
  switch (priority) {
    case 'critical': return '#ef4444' // red
    case 'high': return '#f97316' // orange
    case 'medium': return '#eab308' // yellow
    case 'low': return '#22c55e' // green
  }
}

export function getStatusColor(status: FolderStatistics['projectStatus']): string {
  switch (status) {
    case 'ahead': return '#22c55e' // green
    case 'on-track': return '#3b82f6' // blue
    case 'at-risk': return '#eab308' // yellow
    case 'behind': return '#ef4444' // red
  }
}
