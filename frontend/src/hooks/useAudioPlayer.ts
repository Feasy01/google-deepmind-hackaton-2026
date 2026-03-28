import { useState, useRef, useCallback, useEffect } from 'react'

export interface AudioPlayer {
  play: (url: string) => void
  pause: () => void
  resume: () => void
  stop: () => void
  seek: (time: number) => void
  isPlaying: boolean
  currentTime: number
  duration: number
}

export function useAudioPlayer(): AudioPlayer {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.src = ''
        audioRef.current = null
      }
    }
  }, [])

  const ensureAudio = useCallback(() => {
    if (!audioRef.current) {
      const audio = new Audio()
      audio.addEventListener('timeupdate', () => {
        setCurrentTime(audio.currentTime)
      })
      audio.addEventListener('durationchange', () => {
        setDuration(audio.duration)
      })
      audio.addEventListener('ended', () => {
        setIsPlaying(false)
      })
      audio.addEventListener('pause', () => {
        setIsPlaying(false)
      })
      audio.addEventListener('play', () => {
        setIsPlaying(true)
      })
      audioRef.current = audio
    }
    return audioRef.current
  }, [])

  const play = useCallback(
    (url: string) => {
      const audio = ensureAudio()
      audio.src = url
      audio.play()
    },
    [ensureAudio],
  )

  const pause = useCallback(() => {
    audioRef.current?.pause()
  }, [])

  const resume = useCallback(() => {
    audioRef.current?.play()
  }, [])

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      setCurrentTime(0)
    }
  }, [])

  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time
      setCurrentTime(time)
    }
  }, [])

  return { play, pause, resume, stop, seek, isPlaying, currentTime, duration }
}
