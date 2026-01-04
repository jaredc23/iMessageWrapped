import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import fetchData from '../utils/dataFetcher';
import { formatCount, monthlyTicksFromLabels } from '../utils/numberFormatter';
import { ThemeContext } from '../context/ThemeContext';
import LoadingDots from './LoadingDots';

const Top5ChatsTimeline = () => {
  const [chartData, setChartData] = useState(null);
  const [series, setSeries] = useState([]);
  const [chartKey, setChartKey] = useState(0);

  useEffect(() => {
    const getData = async () => {
      const data = await fetchData();
      if (!data) return;

      const labels = data.top_chats_timeline?.dates || data.topChats?.labels || [];
      const topNames = (data.top_n_chats_by_messages || []).slice(0,5).map(i => (typeof i === 'string' ? i : i[0]));
      const conversations = data.top_chats_timeline?.conversations || {};

      if (!labels || !labels.length) return;

      const s = topNames.map((name, idx) => ({ key: `c${idx}`, name }));

      const formatted = labels.map((label, idx) => {
        const row = { label };
        s.forEach(({ key, name }) => {
          const arr = conversations[name] || [];
          row[key] = typeof arr[idx] === 'number' ? arr[idx] : (arr[idx] ? Number(arr[idx]) : 0);
        });
        return row;
      });

      setSeries(s);
      setChartData(formatted);
      setChartKey(k => k + 1);
    };
    getData();
  }, []);

  if (!chartData) return <LoadingDots />;

  const { theme } = React.useContext(ThemeContext);
  const colors = theme === 'light'
    ? ['#8884d8', '#10b981', '#ff9f40', '#6d28d9', '#ef4444']
    : ['#8884d8', '#82ca9d', '#ff7300', '#413ea0', '#ff6361'];

  // map each date to a month ordinal (0..11) plus fractional day, and add a tiny per-year offset
  const yearValues = chartData.map(r => {
    try { const d = new Date(r.label); return isNaN(d) ? null : d.getFullYear(); } catch (e) { return null; }
  }).filter(y => y !== null);
  const baseYear = yearValues.length ? Math.min(...yearValues) : 0;
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
        const yearOffset = (year - baseYear) * 0.001; // tiny offset per year to avoid identical x
        out.x = month + fraction + yearOffset;
      } else {
        out.x = null;
      }
    } catch (e) { out.x = null; }
    return out;
  }).filter(r => r.x !== null);

  // ensure data is sorted by x (left-to-right chronological)
  displayedData.sort((a, b) => (a.x || 0) - (b.x || 0));

  // Always show Jan..Dec month ticks (0..11) so x-axis labels match EmojiTimeline
  const monthTicksNumeric = Array.from({ length: 12 }, (_, i) => i);
  // determine active series (those with any non-null value)
  const activeSeries = series.map(s => displayedData.some(r => r[s.key] !== null && r[s.key] !== undefined));

  return (
    <div className="slide">
      <h1>Top 5 Chats by Messages</h1>
      <ul>
        {series.slice(0,5).map((s, idx) => (
          <li key={idx}>{s.name}</li>
        ))}
      </ul>
      <div className="panel" style={{ height: '400px' }}>
        <div className="panel-inner">
              <ResponsiveContainer width="100%" height="100%">
              <LineChart key={chartKey} data={displayedData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme === 'light' ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.06)'} />
                <XAxis dataKey="x" type="number" domain={[0,11]} tick={{ fill: theme === 'light' ? '#000' : '#fff' }} ticks={monthTicksNumeric} tickFormatter={(v) => {
                  try { const d = new Date(2000, Math.floor(v), 1); return d.toLocaleString(undefined, { month: 'short' }); } catch (e) { return v; }
                }} />
                <YAxis tickFormatter={v => formatCount(v)} />
                <Tooltip formatter={(value) => [formatCount(value), 'Messages']} labelFormatter={(xVal) => {
                  try {
                    const nearest = displayedData.reduce((best, cur) => Math.abs(cur.x - xVal) < Math.abs(best.x - xVal) ? cur : best, displayedData[0]);
                    return nearest ? nearest.label : '';
                  } catch (e) { return xVal; }
                }} contentStyle={{ background: theme === 'light' ? '#ffffff' : '#1f2937', border: 'none' }} />
                <Legend wrapperStyle={{ fontSize: 18, color: theme === 'light' ? '#000' : '#fff' }} />
                {series.map((sItem, i) => (
                  <Line
                    key={sItem.key}
                    type="linear"
                    dataKey={sItem.key}
                    name={sItem.name}
                    stroke={colors[i % colors.length]}
                    dot={false}
                    strokeWidth={2}
                    isAnimationActive={true}
                    animationBegin={i * 60}
                    animationDuration={900}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Top5ChatsTimeline;
