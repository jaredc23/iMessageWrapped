const path = require('path');
const data = require(path.resolve(__dirname, '../public/wrapped_2025.json'));
const topEmojis = (data.top_emojis_data || data.topEmojisData || [])[0] || [];
const topN = topEmojis.slice(0, 5).map(e => (typeof e === 'string' ? e.trim() : e));
const labels = data.emoji_timeline?.dates || data.emojiTimeline?.labels || [];
const emojisObj = data.emoji_timeline?.emojis || data.emojiTimeline?.emojis || {};
const series = topN.map((emoji, idx) => ({ key: `e${idx}`, emoji }));
const formatted = labels.map((label, idx) => {
  const row = { label };
  series.forEach(({ key, emoji }) => {
    const arr = emojisObj?.[emoji] || [];
    row[key] = typeof arr[idx] === 'number' ? arr[idx] : (arr[idx] ? Number(arr[idx]) : 0);
  });
  return row;
});
const totals = series.map(s => formatted.reduce((acc, r) => acc + (Number(r[s.key]) || 0), 0));
console.log('series:', series.map(s => s.emoji));
console.log('totals:', totals);
console.log('rows:', formatted.length);
console.log('firstRow:', formatted[0]);
console.log('lastRow:', formatted[formatted.length - 1]);
