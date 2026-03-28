export interface Podcast {
  id: string
  filename: string
}

export async function fetchPodcasts(): Promise<Podcast[]> {
  const res = await fetch('/api/podcast/')
  if (!res.ok) throw new Error('Failed to fetch podcasts')
  return res.json()
}

export function getPodcastAudioUrl(id: string): string {
  return `/api/podcast/${encodeURIComponent(id)}/audio`
}
