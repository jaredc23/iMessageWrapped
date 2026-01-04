import React, { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import fetchData from '../utils/dataFetcher';
import { formatCount, formatHourLabel } from '../utils/numberFormatter';
import { ThemeContext } from '../context/ThemeContext';
import LoadingDots from './LoadingDots';

const MessagesSentByHourSlide = () => {
  const [chartData, setChartData] = useState(null);
  const [chartKey, setChartKey] = useState(0);

  useEffect(() => {
    const getData = async () => {
      const fetchedData = await fetchData();
      if (fetchedData) {
        let labels = [];
        let values = [];
        if (fetchedData.messages_sent_by_hour) {
          labels = fetchedData.messages_sent_by_hour.hours || [];
          values = fetchedData.messages_sent_by_hour.counts || [];
        } else if (fetchedData.messagesByHour) {
          labels = fetchedData.messagesByHour.labels || [];
          values = fetchedData.messagesByHour.values || [];
        }

        if (labels.length && values.length) {
          const formatted = labels.map((label, i) => ({ label, value: values[i] }));
          setChartData(formatted);
          setChartKey(prev => prev + 1);
        } else {
          console.warn('MessagesSentByHourSlide: no messages-by-hour data', fetchedData);
        }
      }
    };
    getData();
  }, []);

  if (!chartData) return <LoadingDots />;

  const { theme } = React.useContext(ThemeContext);
  const stroke = theme === 'light' ? '#2563EB' : '#EC4899';
  const fill = theme === 'light' ? 'rgba(37,99,235,0.12)' : 'rgba(236,72,153,0.18)';
  const gridStroke = theme === 'light' ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.06)';
  const tickColor = theme === 'light' ? '#000000' : '#ffffff';

  // Use a centered, constrained container like other slides to avoid overflow
  return (
    <div className="slide">
      <h1>Average Number of Messages Sent, by Hour</h1>
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <div style={{ height: '400px', width: '100%', maxWidth: 720, overflow: 'hidden', margin: '0 auto' }} className="panel">
          <div className="panel-inner">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart key={chartKey} data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                  <XAxis dataKey="label" tick={{ fill: tickColor }} tickFormatter={(v) => {
                  const n = Number(v);
                  if (!isNaN(n) && n >= 0 && n <= 23) return formatHourLabel(n);
                  return v;
                }} ticks={(chartData || []).map(r => r.label)} />
                  <YAxis tickFormatter={v => formatCount(v)} />
                  <Tooltip formatter={(value) => [formatCount(value), 'Messages']} contentStyle={{ background: theme === 'light' ? '#ffffff' : '#1f2937', border: 'none' }} />
                  <Area type="linear" name="Messages" dataKey="value" stroke={stroke} fill={fill} strokeWidth={3} dot={false} isAnimationActive={true} animationBegin={0} animationDuration={900} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessagesSentByHourSlide;