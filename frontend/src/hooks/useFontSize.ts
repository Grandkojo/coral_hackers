import { useEffect, useState } from 'react'
import { getHeroSize } from '../utils/responsive'

export const useHeroFontSize = () => {
  const [heroFontSize, setHeroFontSize] = useState(() =>
    typeof window !== 'undefined'
      ? getHeroSize(window.innerWidth)
      : 300,
  )

  useEffect(() => {
    const onResize = () => {
      setHeroFontSize(getHeroSize(window.innerWidth))
    }

    window.addEventListener('resize', onResize)

    return () => {
      window.removeEventListener('resize', onResize)
    }
  }, [])

  return heroFontSize
}