import { http } from '@/shared/api/http'
import type {
  AnalysisCatalog,
  AnalysisFacetRequest,
  AnalysisFacetResult,
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

export async function postAnalysisFacets(
  request: AnalysisFacetRequest,
): Promise<AnalysisFacetResult> {
  const response = await http.post<AnalysisFacetResult>(
    '/manual-qc/analysis/facets',
    request,
  )
  return response.data
}
