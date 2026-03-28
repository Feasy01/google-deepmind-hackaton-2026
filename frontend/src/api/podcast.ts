export interface Episode {
  id: string
  name: string
  filename: string
}

export interface Podcaster {
  podcaster: string
  categories: string[]
  description: string
  episodes: Episode[]
}

export async function fetchPodcasters(): Promise<Podcaster[]> {
  const res = await fetch('/api/podcast/')
  if (!res.ok) throw new Error('Failed to fetch podcasters')
  return res.json()
}

export function getPodcastAudioUrl(podcaster: string, episodeId: string): string {
  return `/api/podcast/${encodeURIComponent(podcaster)}/${encodeURIComponent(episodeId)}/audio`
}
