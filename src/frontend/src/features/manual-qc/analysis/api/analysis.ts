import { http } from '@/shared/api/http'
import type {
  AnalysisCatalog,
  AnalysisQuery,
  AnalysisQueryResult,
} from '../types/analysis'

export async function getAnalysisCatalog(): Promise<AnalysisCatalog> {
  const response = await http.get<AnalysisCatalog>('/manual-qc/analysis/catalog')
  return response.data
}

export async function postAnalysisQuery(
  query: AnalysisQuery,
): Promise<AnalysisQueryResult> {
  const response = await http.post<AnalysisQueryResult>(
    '/manual-qc/analysis/query',
    query,
  )
  return response.data
}
