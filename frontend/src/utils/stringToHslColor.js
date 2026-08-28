/**
 * Генерирует пастельный HSL-цвет из строки.
 * Используется для цветных фонов тегов.
 * @param {string} str - Название тега
 * @returns {string} HSL-цвет в формате hsl(hue, saturation, lightness)
 */
export function stringToHslColor(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 31 + str.charCodeAt(i)) | 0
  }
  hash = Math.abs(hash)
  const hue = hash % 360
  return `hsl(${hue}, 80%, 90%)`
}
