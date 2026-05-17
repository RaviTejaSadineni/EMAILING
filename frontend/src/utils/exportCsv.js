/**
 * Export an array of objects as a CSV file download.
 * @param {string} filename  – Name of the downloaded file (with .csv extension)
 * @param {Array<Object>} rows – Array of flat objects
 * @param {string[]} [columns] – Optional ordered column keys; defaults to all keys of first row
 */
export default function exportCsv(filename, rows, columns) {
  if (!rows?.length) return

  const cols = columns || Object.keys(rows[0])

  const escape = (val) => {
    if (val == null) return ''
    const str = String(val)
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`
    }
    return str
  }

  const header = cols.map(escape).join(',')
  const body = rows.map((row) => cols.map((c) => escape(row[c])).join(',')).join('\n')
  const csv = `${header}\n${body}`

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
