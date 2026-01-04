import React, { useContext } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatCount } from '../utils/numberFormatter';
import { ThemeContext } from '../context/ThemeContext';

const MessagesTimelineChart = ({ formatted, height = 400 }) => {
  if (!Array.isArray(formatted) || !formatted.length) return <p>No timeline data.</p>;

  const { theme } = useContext(ThemeContext);
  const stroke = theme === 'light' ? '#2563EB' : '#EC4899';
  const fill = theme === 'light' ? 'rgba(37,99,235,0.12)' : 'rgba(236,72,153,0.18)';
  const gridStroke = theme === 'light' ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.06)';
  const tickColor = theme === 'light' ? '#000000' : '#ffffff';

  // map values and compute numeric month x (month + fractional day) like EmojiTimeline
  const mapped = formatted.map(row => ({ label: row.label, value: Number(row.value) || 0 }));

  const displayed = mapped.map(row => {
    const out = { ...row };
    try {
      const d = new Date(row.label);
      if (!isNaN(d)) {
        const year = d.getFullYear();
        if (year !== 2025) { out.x = null; }
        else {
          const month = d.getMonth();
          const day = d.getDate();
          const daysInMonth = new Date(year, month + 1, 0).getDate();
          const fraction = daysInMonth > 1 ? (day - 1) / daysInMonth : 0;
          out.x = month + fraction;
        }
      } else {
        out.x = null;
      }
    } catch (e) { out.x = null; }
    return out;
  }).filter(r => r.x !== null);

  const monthTicksNumeric = Array.from({ length: 12 }, (_, i) => i);

  return (
    <div style={{ height, width: '100%' }}>
      <div style={{ height: '100%', width: '100%', background: 'transparent' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={displayed} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
              <XAxis dataKey="x" type="number" domain={[0,11]} tick={{ fill: tickColor }} ticks={monthTicksNumeric} tickFormatter={(v) => {
                try { const d = new Date(2000, Math.floor(v), 1); return d.toLocaleString(undefined, { month: 'short' }); } catch (e) { return v; }
              }} />
              <YAxis tickFormatter={v => formatCount(v)} />
              <Tooltip formatter={(value) => [formatCount(value), 'Messages']} labelFormatter={(xVal) => {
                try {
                  const nearest = displayed.reduce((best, cur) => Math.abs(cur.x - xVal) < Math.abs(best.x - xVal) ? cur : best, displayed[0]);
                  return nearest ? nearest.label : '';
                } catch (e) { return xVal; }
              }} contentStyle={{ background: theme === 'light' ? '#ffffff' : '#1f2937', border: 'none' }} />
              <Area type="linear" dataKey="value" name="Messages" stroke={stroke} fill={fill} strokeWidth={3} dot={false} isAnimationActive={true} animationBegin={0} animationDuration={900} />
            </AreaChart>
          </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MessagesTimelineChart;
