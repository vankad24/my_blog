function stringToIntHash(str) {
  let hash = 2166136261

  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }

  return hash >>> 0
}

/**
 * Генерирует hue (0-359) из строки.
 * Используется для цвета текста и фонов.
 * @param {string} str - Название тега
 * @returns {number} Hue значение от 0 до 359
 */
export function stringToHue(str) {
  return stringToIntHash(str) % 360
}
