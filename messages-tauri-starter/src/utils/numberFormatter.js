export function withCommas(x) {
  if (x === null || x === undefined || x === '') return '—';
  const n = Number(x);
  if (!isFinite(n)) return String(x);
  const parts = Math.abs(n).toFixed(0).split('');
  let i = parts.length - 3;
  while (i > 0) {
    parts.splice(i, 0, ',');
    i -= 3;
  }
  const sign = n < 0 ? '-' : '';
  return sign + parts.join('');
}

export function roundToTwo(n) {
  if (n === null || n === undefined || n === '') return '—';
  const num = Number(n);
  if (!isFinite(num)) return String(n);
  return (Math.round(num * 100) / 100).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

export function formatCount(n) {
  if (n === null || n === undefined || n === '') return '—';
  const num = Number(n);
  if (!isFinite(num)) return String(n);
  return num % 1 === 0 ? withCommas(num) : roundToTwo(num);
}

export function formatMinutesOrSeconds(mins) {
  if (mins === null || mins === undefined || mins === '') return '—';
  const n = Number(mins);
  if (!isFinite(n)) return String(mins);
  // Prefer larger units when values are large to avoid huge minute counts
  if (n >= 1440) { // days
    const days = n / 1440;
    const disp = roundToTwo(days);
    const isOne = Math.abs(days - 1) < 0.005;
    return `${disp} day${isOne ? '' : 's'}`;
  }
  if (n >= 60) { // hours
    const hours = n / 60;
    const disp = roundToTwo(hours);
    const isOne = Math.abs(hours - 1) < 0.005;
    return `${disp} hr${isOne ? '' : 's'}`;
  }
  if (n >= 1) {
    return `${roundToTwo(n)} min`;
  }
  const secs = Math.round(n * 60);
  return `${withCommas(secs)} sec`;
}

export function formatHourLabel(hour) {
  // Accept numbers or numeric strings 0-23
  if (hour === null || hour === undefined || hour === '') return '';
  const h = Number(hour);
  if (!Number.isFinite(h)) return String(hour);
  const mod = ((h % 24) + 24) % 24;
  const suffix = mod === 0 ? 'AM' : mod < 12 ? 'AM' : 'PM';
  let display = mod % 12 === 0 ? 12 : mod % 12;
  return `${display}${suffix}`;
}

export function monthlyTicksFromLabels(labels) {
  // labels: array of ISO date strings (e.g., '2025-01-20') or Date objects.
  // Return up to 12 tick label values, one per month, selecting the first available label on or after the 1st of each month.
  if (!Array.isArray(labels) || labels.length === 0) return [];
  // Parse labels into Date objects and keep the original string
  const parsed = labels.map((l, i) => {
    let d = null;
    if (l instanceof Date) d = l;
    else {
      d = new Date(l);
      if (isNaN(d)) d = null;
    }
    return { orig: labels[i], date: d };
  }).filter(x => x.date);
  if (!parsed.length) return [];

  // Determine calendar year to show ticks for: use the year of the first available date
  const sorted = parsed.slice().sort((a,b) => a.date - b.date);
  const start = sorted[0].date;

  // Build list of the 12 month starts for the calendar year of the first data point
  const startYear = start.getFullYear();
  const months = [];
  for (let m = 0; m < 12; m++) {
    months.push(new Date(startYear, m, 1));
  }

  // Return canonical first-of-month ISO strings (YYYY-MM-DD) for each month Jan..Dec of startYear
  const pad = (n) => String(n).padStart(2, '0');
  const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
  const ticks = months.map(m => iso(m));
  return ticks.slice(0, 12);
}

export default { withCommas, roundToTwo, formatCount, formatMinutesOrSeconds, formatHourLabel, monthlyTicksFromLabels };
