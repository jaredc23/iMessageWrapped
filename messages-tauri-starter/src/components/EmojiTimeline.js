import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import fetchData from '../utils/dataFetcher';
import { formatCount } from '../utils/numberFormatter';
import { ThemeContext } from '../context/ThemeContext';
import LoadingDots from './LoadingDots';

const EmojiTimeline = () => {
  const [chartData, setChartData] = useState(null);
  const [emojis, setEmojis] = useState([]);
  const [chartKey, setChartKey] = useState(0);

  useEffect(() => {
    const getData = async () => {
      const data = await fetchData();
      if (!data) return;

      const topEmojis = data.top_emojis_data?.[0] || data.topEmojisData?.[0] || [];
      const topN = topEmojis.slice(0, 5).map((e) => (typeof e === 'string' ? e.trim() : e));

      const labels = data.emoji_timeline?.dates || data.emojiTimeline?.labels || [];
      const emojisObj = data.emoji_timeline?.emojis || data.emojiTimeline?.emojis || {};

      if (!labels || !labels.length) return;

      const series = topN.map((emoji, idx) => ({ key: `e${idx}`, emoji }));

      const formatted = labels.map((label, idx) => {
        const row = { label };
        series.forEach(({ key, emoji }) => {
          const arr = emojisObj?.[emoji] || [];
          row[key] = typeof arr[idx] === 'number' ? arr[idx] : (arr[idx] ? Number(arr[idx]) : 0);
        });
        return row;
      });

      setChartData(formatted);
      setEmojis(series);
      setChartKey(prev => prev + 1);
    };
    getData();
  }, []);

  if (!chartData) return <LoadingDots />;

  const { theme } = React.useContext(ThemeContext);
  const colors = theme === 'light'
    ? ['#F97316', '#0EA5A4', '#2563EB', '#7C3AED', '#EF4444', '#10B981']
    : ['#FF9F40', '#4BC0C0', '#36A2EB', '#9966FF', '#FF6384', '#8DD3C7'];

  const displayedData = chartData.map(row => {
    const out = { ...row };
    try {
      const d = new Date(row.label);
      if (!isNaN(d)) {
        const year = d.getFullYear();
        const month = d.getMonth();
        const day = d.getDate();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const fraction = daysInMonth > 1 ? (day - 1) / daysInMonth : 0;
        out.x = month + fraction;
      } else {
        out.x = null;
      }
    } catch (e) { out.x = null; }
    return out;
  }).filter(r => r.x !== null);

  const monthTicksNumeric = Array.from({ length: 12 }, (_, i) => i);

  return (
    <div className="slide">
      <h1>Emoji Timeline</h1>
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <div style={{ height: '400px', width: '100%', maxWidth: 720, boxSizing: 'border-box', overflow: 'hidden', margin: '0 auto' }} className="panel">
          <div className="panel-inner">
              <ResponsiveContainer width="100%" height="100%">
              <LineChart key={chartKey} data={displayedData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="x" type="number" domain={[0,11]} tick={{ fill: theme === 'light' ? '#000' : '#fff' }} ticks={monthTicksNumeric} tickFormatter={(v) => {
                  try { const d = new Date(2000, Math.floor(v), 1); return d.toLocaleString(undefined, { month: 'short' }); } catch (e) { return v; }
                }} />
                <YAxis tickFormatter={v => formatCount(v)} />
                <Tooltip formatter={(value, name) => [formatCount(value), name]} labelFormatter={(xVal) => {
                  try {
                    const nearest = displayedData.reduce((best, cur) => Math.abs(cur.x - xVal) < Math.abs(best.x - xVal) ? cur : best, displayedData[0]);
                    return nearest ? nearest.label : '';
                  } catch (e) { return xVal; }
                }} contentStyle={{ background: theme === 'light' ? '#ffffff' : '#1f2937', border: 'none' }} />
                <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: 18, color: 'white' }} />
                {emojis.map((s, i) => (
                  <Line
                    key={s.key}
                    type="linear"
                    dataKey={s.key}
                    name={s.emoji}
                    stroke={colors[i % colors.length]}
                    dot={false}
                    strokeWidth={2}
                    isAnimationActive={true}
                    animationBegin={i * 80}
                    animationDuration={900}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmojiTimeline;
