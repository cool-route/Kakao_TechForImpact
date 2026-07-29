// Placeholder API interfaces for future backend integration.
// Replace simulated calls in components with real fetch requests to these functions.

export type AnalyzeResponse = {
  tags: string[];
};

export async function analyzeTranscript(text: string): Promise<AnalyzeResponse> {
  // Example implementation when backend is ready:
  // const res = await fetch('/api/analyze', { method: 'POST', body: JSON.stringify({ text }) });
  // return res.json();

  // Temporary fake response for frontend development
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ tags: ['#시민한갈길', '#30분', '#반려동물'] });
    }, 800);
  });
}

export type RecommendRoutesResponse = {
  routes: Array<{ id: string; name: string; distance: number; duration_minutes: number }>
}

export async function recommendRoutes(tags: string[]): Promise<RecommendRoutesResponse> {
  // Example when backend API exists:
  // const res = await fetch('/api/recommend', { method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ tags }) });
  // return res.json();

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ routes: [
        { id: 'r1', name: '시민한강길 A코스', distance: 2.1, duration_minutes: 30 },
        { id: 'r2', name: '시민한강길 B코스', distance: 3.1, duration_minutes: 38 },
        { id: 'r3', name: '올림픽공원 산책로', distance: 2.8, duration_minutes: 35 },
      ]});
    }, 600);
  });
}
