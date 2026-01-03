// Project-level insights ported from v0-employee-tracking/data/projects-insights.ts
// Used for the Projects / Project Insights sections in the timesheet dashboard.

export interface ProjectInsight {
  id: string
  name: string
  plannedHours: number
  actualHours: number
  percentComplete: number
  status: 'On Track' | 'At Risk' | 'Behind'
  weeksInProgress: number
  startDate: string
  timeline: Array<{
    week: number
    planned: number
    actual: number
  }>
}

export const projectInsights: ProjectInsight[] = [
  {
    id: '25-04-147',
    name: 'Downtown Office Tower',
    plannedHours: 120,
    actualHours: 118,
    percentComplete: 85,
    status: 'On Track',
    weeksInProgress: 6,
    startDate: '2024-10-14',
    timeline: [
      { week: 1, planned: 20, actual: 18 },
      { week: 2, planned: 30, actual: 28 },
      { week: 3, planned: 45, actual: 43 },
      { week: 4, planned: 75, actual: 76 },
      { week: 5, planned: 95, actual: 93 },
      { week: 6, planned: 120, actual: 118 },
    ],
  },
  {
    id: '25-06-167',
    name: 'Industrial Warehouse Expansion',
    plannedHours: 215,
    actualHours: 125,
    percentComplete: 55,
    status: 'Behind',
    weeksInProgress: 8,
    startDate: '2024-09-30',
    timeline: [
      { week: 1, planned: 25, actual: 20 },
      { week: 2, planned: 40, actual: 30 },
      { week: 3, planned: 60, actual: 42 },
      { week: 4, planned: 85, actual: 58 },
      { week: 5, planned: 110, actual: 72 },
      { week: 6, planned: 140, actual: 88 },
      { week: 7, planned: 175, actual: 105 },
      { week: 8, planned: 215, actual: 125 },
    ],
  },
  {
    id: '25-03-132',
    name: 'Residential Podium Building',
    plannedHours: 60,
    actualHours: 48,
    percentComplete: 75,
    status: 'At Risk',
    weeksInProgress: 4,
    startDate: '2024-10-28',
    timeline: [
      { week: 1, planned: 15, actual: 12 },
      { week: 2, planned: 25, actual: 20 },
      { week: 3, planned: 40, actual: 32 },
      { week: 4, planned: 60, actual: 48 },
    ],
  },
  {
    id: '25-05-153',
    name: 'Retail Strip Mall',
    plannedHours: 50,
    actualHours: 52,
    percentComplete: 95,
    status: 'On Track',
    weeksInProgress: 3,
    startDate: '2024-11-04',
    timeline: [
      { week: 1, planned: 18, actual: 20 },
      { week: 2, planned: 32, actual: 35 },
      { week: 3, planned: 50, actual: 52 },
    ],
  },
  {
    id: '25-07-178',
    name: 'School Addition',
    plannedHours: 20,
    actualHours: 21,
    percentComplete: 100,
    status: 'On Track',
    weeksInProgress: 2,
    startDate: '2024-11-11',
    timeline: [
      { week: 1, planned: 10, actual: 11 },
      { week: 2, planned: 20, actual: 21 },
    ],
  },
  {
    id: '25-02-089',
    name: 'Hospital Seismic Retrofit',
    plannedHours: 105,
    actualHours: 78,
    percentComplete: 70,
    status: 'Behind',
    weeksInProgress: 5,
    startDate: '2024-10-21',
    timeline: [
      { week: 1, planned: 22, actual: 18 },
      { week: 2, planned: 38, actual: 30 },
      { week: 3, planned: 58, actual: 45 },
      { week: 4, planned: 80, actual: 60 },
      { week: 5, planned: 105, actual: 78 },
    ],
  },
]

export function computeProjectStatus(actualHours: number, plannedHours: number): ProjectInsight['status'] {
  const ratio = actualHours / plannedHours

  if (ratio >= 0.9 && ratio <= 1.0) return 'On Track'
  if (ratio > 0.8 && ratio < 0.9) return 'At Risk'
  if (ratio >= 1.0 && ratio <= 1.1) return 'At Risk'
  return 'Behind'
}







