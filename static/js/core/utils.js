export function formatDateDMY(value) {
  try {
    const d = new Date(value);
    if (isNaN(d)) return value || '';
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    return `${dd}/${mm}/${yyyy}`;
  } catch {
    return value || '';
  }
}
