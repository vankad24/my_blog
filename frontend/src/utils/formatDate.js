/**
 * Названия месяцев в родительном падеже (для дат вида "17 августа").
 * toLocaleDateString('ru-RU', { month: 'long' }) может давать непредсказуемый результат
 * в некоторых браузерах, поэтому используем фиксированный массив.
 */
const MONTHS = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
]

/**
 * Парсит строку даты в объект Date.
 * Обрабатывает ISO-формат, разное время и UTC.
 */
function parseDate(dateStr) {
  if (!dateStr) return null
  // ISO 8601 с timezone (2024-01-10T16:40:00Z или 2024-01-10T16:40:00+03:00)
  // ISO 8601 без timezone (2024-01-10T16:40:00)
  // Пробел вместо T (2024-01-10 16:40:00)
  const normalized = dateStr.replace(' ', 'T')
  const d = new Date(normalized)
  // Если парсинг не удался — пробуем как есть
  if (isNaN(d.getTime())) {
    return new Date(dateStr)
  }
  return d
}

/**
 * Форматирует дату в относительном формате.
 * - Сегодня: "Сегодня 16:40"
 * - Этот год: "10 июня 12:23"
 * - Прошлые годы: "2 января 18:27 2024 г."
 *
 * Время всегда отображается в часовом поясе пользователя (браузера).
 * Если дата пришла в UTC — она автоматически конвертируется в локальное время.
 */
export function formatRelativeDate(dateStr) {
  const date = parseDate(dateStr)
  if (!date) return ''

  const now = new Date()

  // Определяем "сегодня" и "эту неделю" по локальной дате пользователя
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const diffDays = Math.floor((today - new Date(date.getFullYear(), date.getMonth(), date.getDate())) / (1000 * 60 * 60 * 24))

  const timeStr = date.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  })

  if (diffDays === 0) {
    return `Сегодня ${timeStr}`
  }

  if (diffDays === 1) {
    return `Вчера ${timeStr}`
  }

  if (diffDays < 7) {
    // Склонение: 1 день назад, 2 дня назад, 3 дня назад...
    const dayCount = diffDays
    let dayWord
    if (dayCount % 10 === 1 && dayCount % 100 !== 11) {
      dayWord = 'день назад'
    } else if ((dayCount % 10 >= 2 && dayCount % 10 <= 4) && (dayCount % 100 < 10 || dayCount % 100 >= 20)) {
      dayWord = 'дня назад'
    } else {
      dayWord = 'дней назад'
    }
    return `${dayCount} ${dayWord} ${timeStr}`
  }

  // Родительный падеж для месяцев: "17 августа", "10 июня"
  const month = MONTHS[date.getMonth()]
  const base = `${date.getDate()} ${month} ${timeStr}`

  if (date.getFullYear() !== now.getFullYear()) {
    return `${base} ${date.getFullYear()} г.`
  }

  return base
}
