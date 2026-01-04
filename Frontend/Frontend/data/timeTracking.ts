// Time tracking data ported from v0 employee tracking demo.
// This is a trimmed, frontend-only dataset used to power the SidOS timesheet views.
// If you update the v0 demo data, mirror any important changes here.

export interface TimeEvent {
  employeeId: string
  task: string
  subtask: string
  project: string
  app: string
  duration: number // minutes
  timestamp: string
  startTime: string
  endTime: string
}

export interface TimeProjectTask {
  name: string
  value: number
}

export interface TimeProjectEmployee {
  id: string
  name: string
  hours: number
}

export interface TimeProject {
  id: string
  name: string
  totalHours: number
  employees: TimeProjectEmployee[]
  tasks: TimeProjectTask[]
  client?: string
  clientRelationship?: 'Excellent' | 'Good' | 'Standard'
  status?: 'On Track' | 'At Risk' | 'Behind'
}

// NOTE: This is a direct copy of the "projects" array from
// /v0-employee-tracking/data/mock-data.ts, minus type-specific TS syntax.
export const timeProjects: TimeProject[] = [
  {
    id: '25-04-147',
    name: 'Downtown Office Tower',
    totalHours: 49,
    client: 'Urban Development Corp',
    clientRelationship: 'Excellent',
    status: 'On Track',
    employees: [
      { id: 'emp1', name: 'Sarah Chen', hours: 18 },
      { id: 'emp3', name: 'Emily Watson', hours: 20 },
      { id: 'emp5', name: 'Aisha Patel', hours: 11 },
    ],
    tasks: [
      { name: 'RISA Modeling', value: 14 },
      { name: 'Revit Modeling', value: 14 },
      { name: 'ETABS Analysis', value: 6 },
      { name: 'Report Writing', value: 6 },
      { name: 'Revit Edits', value: 4 },
      { name: 'Drawing Production', value: 4 },
      { name: 'Site Visit', value: 3 },
      { name: 'Email Coordination', value: 2 },
    ],
  },
  {
    id: '25-06-167',
    name: 'Industrial Warehouse Expansion',
    totalHours: 38,
    employees: [
      { id: 'emp1', name: 'Sarah Chen', hours: 10 },
      { id: 'emp2', name: 'Michael Rodriguez', hours: 12 },
      { id: 'emp4', name: 'James Park', hours: 16 },
    ],
    tasks: [
      { name: 'Design Mezzanine', value: 8 },
      { name: 'RISA Modeling', value: 6 },
      { name: 'ETABS Analysis', value: 5 },
      { name: 'Foundation System', value: 5 },
      { name: 'Connection Design', value: 4 },
      { name: 'Foundation Design', value: 3 },
      { name: 'Lateral Analysis', value: 3 },
      { name: 'Drawing Review', value: 2 },
      { name: 'Drawing Markup', value: 2 },
    ],
  },
  {
    id: '25-03-132',
    name: 'Residential Podium Building',
    totalHours: 32,
    employees: [
      { id: 'emp2', name: 'Michael Rodriguez', hours: 15 },
      { id: 'emp5', name: 'Aisha Patel', hours: 17 },
    ],
    tasks: [
      { name: 'SAFE Modeling', value: 16 },
      { name: 'Lateral System Design', value: 5 },
      { name: 'Concrete Design', value: 5 },
      { name: 'Drawing Review', value: 3 },
      { name: 'Report Writing', value: 3 },
    ],
  },
  {
    id: '25-05-153',
    name: 'Retail Strip Mall',
    totalHours: 26,
    employees: [
      { id: 'emp3', name: 'Emily Watson', hours: 8 },
      { id: 'emp6', name: 'David Kim', hours: 18 },
    ],
    tasks: [
      { name: 'Revit Modeling', value: 10 },
      { name: 'Drawing Production', value: 6 },
      { name: 'ETABS Modeling', value: 5 },
      { name: 'Report Assistance', value: 3 },
      { name: 'Markup Revisions', value: 2 },
    ],
  },
  {
    id: '25-07-178',
    name: 'School Addition',
    totalHours: 24,
    employees: [
      { id: 'emp4', name: 'James Park', hours: 14 },
      { id: 'emp6', name: 'David Kim', hours: 10 },
    ],
    tasks: [
      { name: 'RISA Modeling', value: 7 },
      { name: 'RISA Input', value: 5 },
      { name: 'Connection Design', value: 4 },
      { name: 'Construction Support', value: 3 },
      { name: 'Calculation Checks', value: 3 },
      { name: 'Drawing Coordination', value: 2 },
    ],
  },
  {
    id: '25-08-192',
    name: 'Commercial Building Upgrade',
    totalHours: 31,
    employees: [
      { id: 'emp7', name: 'Rebecca Martinez', hours: 19 },
      { id: 'emp8', name: 'Kevin Thompson', hours: 21 },
    ],
    tasks: [
      { name: 'RISA Modeling', value: 10 },
      { name: 'Foundation Design', value: 8 },
      { name: 'Drawing Review', value: 3 },
      { name: 'Report Writing', value: 2 },
      { name: 'Site Visit', value: 1 },
    ],
  },
  {
    id: '25-09-201',
    name: 'Office Complex Renovation',
    totalHours: 28,
    employees: [
      { id: 'emp8', name: 'Kevin Thompson', hours: 21 },
      { id: 'emp9', name: 'Lisa Zhang', hours: 16 },
    ],
    tasks: [
      { name: 'Revit Modeling', value: 10 },
      { name: 'Drawing Production', value: 6 },
      { name: 'ETABS Modeling', value: 5 },
      { name: 'Report Assistance', value: 3 },
      { name: 'Markup Revisions', value: 2 },
    ],
  },
]

// For now we only need a subset of the full v0 events dataset to drive the
// timesheet log UI. If you want the complete data, you can copy the remainder
// of the "events" array from the v0 repo.
export const timeEvents: TimeEvent[] = [
  // emp1 - Sarah Chen - sample week
  {
    employeeId: 'emp1',
    task: 'RISA Modeling',
    subtask: 'Beam Design - Grid A',
    project: '25-04-147',
    app: 'RISA-3D',
    duration: 120,
    timestamp: '2025-11-17T08:30:00',
    startTime: '2025-11-17T08:30:00',
    endTime: '2025-11-17T10:30:00',
  },
  {
    employeeId: 'emp1',
    task: 'Meetings',
    subtask: 'Project Kickoff',
    project: '25-04-147',
    app: 'Microsoft Teams',
    duration: 60,
    timestamp: '2025-11-17T13:00:00',
    startTime: '2025-11-17T13:00:00',
    endTime: '2025-11-17T14:00:00',
  },
  {
    employeeId: 'emp1',
    task: 'Admin',
    subtask: 'Timesheet Entry',
    project: 'Admin',
    app: 'Browser',
    duration: 45,
    timestamp: '2025-11-17T15:30:00',
    startTime: '2025-11-17T15:30:00',
    endTime: '2025-11-17T16:15:00',
  },
  {
    employeeId: 'emp1',
    task: 'Site Visit',
    subtask: 'Foundation Inspection',
    project: '25-04-147',
    app: 'Field Work',
    duration: 180,
    timestamp: '2025-11-21T08:00:00',
    startTime: '2025-11-21T08:00:00',
    endTime: '2025-11-21T11:00:00',
  },
  // emp2 - Michael Rodriguez - sample week
  {
    employeeId: 'emp2',
    task: 'SAFE Modeling',
    subtask: 'Slab Layout',
    project: '25-03-132',
    app: 'SAFE',
    duration: 120,
    timestamp: '2025-11-17T08:00:00',
    startTime: '2025-11-17T08:00:00',
    endTime: '2025-11-17T10:00:00',
  },
  {
    employeeId: 'emp2',
    task: 'Lateral System Design',
    subtask: 'Shear Wall Layout',
    project: '25-03-132',
    app: 'AutoCAD',
    duration: 120,
    timestamp: '2025-11-17T14:00:00',
    startTime: '2025-11-17T14:00:00',
    endTime: '2025-11-17T16:00:00',
  },
  {
    employeeId: 'emp2',
    task: 'Admin',
    subtask: 'Project Documentation',
    project: 'Admin',
    app: 'Browser',
    duration: 60,
    timestamp: '2025-11-17T16:00:00',
    startTime: '2025-11-17T16:00:00',
    endTime: '2025-11-17T17:00:00',
  },
  // emp11 - James Hinsperger - current day detailed log (bridge design + RFP work)
  {
    employeeId: 'emp11',
    task: 'Bridge Design – Requirements Review',
    subtask: 'Read client brief & existing drawings',
    project: 'BR-2025-001',
    app: 'Adobe Acrobat',
    duration: 45,
    timestamp: '2025-12-15T08:15:00',
    startTime: '2025-12-15T08:15:00',
    endTime: '2025-12-15T09:00:00',
  },
  {
    employeeId: 'emp11',
    task: 'Bridge Design – Concept Modeling',
    subtask: 'Generate initial parametric geometry',
    project: 'BR-2025-001',
    app: 'Speckle / Revit',
    duration: 120,
    timestamp: '2025-12-15T09:00:00',
    startTime: '2025-12-15T09:00:00',
    endTime: '2025-12-15T11:00:00',
  },
  {
    employeeId: 'emp11',
    task: 'Bridge Design – Structural Analysis',
    subtask: 'Run model in RISA / ETABS and check envelopes',
    project: 'BR-2025-001',
    app: 'RISA-3D / ETABS',
    duration: 90,
    timestamp: '2025-12-15T11:00:00',
    startTime: '2025-12-15T11:00:00',
    endTime: '2025-12-15T12:30:00',
  },
  {
    employeeId: 'emp11',
    task: 'Emails & Teams',
    subtask: 'Coordinate design assumptions with project team',
    project: 'BR-2025-001',
    app: 'Outlook / Teams',
    duration: 40,
    timestamp: '2025-12-15T13:00:00',
    startTime: '2025-12-15T13:00:00',
    endTime: '2025-12-15T13:40:00',
  },
  {
    employeeId: 'emp11',
    task: 'RFP 63023 – Outline',
    subtask: 'Define sections & key win themes',
    project: 'RFP-63023',
    app: 'Microsoft Word',
    duration: 60,
    timestamp: '2025-12-15T13:45:00',
    startTime: '2025-12-15T13:45:00',
    endTime: '2025-12-15T14:45:00',
  },
  {
    employeeId: 'emp11',
    task: 'RFP 63023 – Technical Approach',
    subtask: 'Draft bridge methodology & deliverables',
    project: 'RFP-63023',
    app: 'Microsoft Word',
    duration: 75,
    timestamp: '2025-12-15T14:45:00',
    startTime: '2025-12-15T14:45:00',
    endTime: '2025-12-15T16:00:00',
  },
  {
    employeeId: 'emp11',
    task: 'RFP 63023 – QA / Edits',
    subtask: 'Refine wording, check alignment with key points',
    project: 'RFP-63023',
    app: 'Microsoft Word',
    duration: 45,
    timestamp: '2025-12-15T16:00:00',
    startTime: '2025-12-15T16:00:00',
    endTime: '2025-12-15T16:45:00',
  },
  {
    employeeId: 'emp11',
    task: 'Admin / Timesheets',
    subtask: 'Log work for the day',
    project: 'Admin',
    app: 'Browser',
    duration: 15,
    timestamp: '2025-12-15T16:45:00',
    startTime: '2025-12-15T16:45:00',
    endTime: '2025-12-15T17:00:00',
  },
]



