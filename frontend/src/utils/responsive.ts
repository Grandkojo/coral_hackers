export const getHeroSize = (width: number) => {
  if (width < 480) return 40
  if (width < 768) return 180
  return 300
}