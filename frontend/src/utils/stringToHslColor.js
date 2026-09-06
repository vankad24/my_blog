function hashString(str) {
  let hash = 2166136261;

  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }

  return hash >>> 0;
}

/**
 * Генерирует пастельный HSL-цвет из строки.
 * Используется для цветных фонов тегов.
 * @param {string} str - Название тега
 * @returns {string} HSL-цвет в формате hsl(hue, saturation, lightness)
 */
export function stringToHslColor(str) {
  let hash = hashString(str)
  const hue = hash % 360
  return `hsl(${hue}, 80%, 90%)`
}
