import React, { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import fetchData from '../utils/dataFetcher';
import { roundToTwo, formatHourLabel } from '../utils/numberFormatter';
import { ThemeContext } from '../context/ThemeContext';
import LoadingDots from './LoadingDots';

const WordsPerMessageByHour = () => {
  const [chartData, setChartData] = useState(null);
  const [chartKey, setChartKey] = useState(0);

  useEffect(() => {
    const getData = async () => {
      const data = await fetchData();
      if (data) {
        try {
          let labels = [];
          let values = [];

          if (data.wordsPerMessagePerHour) {
            const w = data.wordsPerMessagePerHour;
            if (Array.isArray(w.hours) && Array.isArray(w.avg_words)) {
              labels = w.hours;
              values = w.avg_words;
            } else if (typeof w === 'object') {
              labels = Object.keys(w);
              values = Object.values(w);
            }
          } else if (data.words_per_message_per_hour) {
            const w = data.words_per_message_per_hour;
            if (Array.isArray(w.hours) && Array.isArray(w.avg_words)) {
              labels = w.hours;
              values = w.avg_words;
            } else if (typeof w === 'object') {
              labels = Object.keys(w);
              values = Object.values(w);
            }
          }

          if (labels.length && values.length) {
            const formatted = labels.map((label, i) => ({ label, value: values[i] }));
            setChartData(formatted);
            setChartKey(prev => prev + 1);
          } else {
            console.warn('WordsPerMessageByHour: no words-per-message data found', data);
          }
        } catch (err) {
          console.error('Error formatting WordsPerMessageByHour data', err, data);
        }
      }
    };
    getData();
  }, []);

  if (!chartData) return <LoadingDots />;

  const { theme } = React.useContext(ThemeContext);
  const stroke = theme === 'light' ? '#8B5CF6' : '#60A5FA';
  const fill = theme === 'light' ? 'rgba(139,92,246,0.2)' : 'rgba(96,165,250,0.15)';
  const gridStroke = theme === 'light' ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.06)';
  const tickColor = theme === 'light' ? '#000000' : '#ffffff';

  return (
    <div className="slide">
      <h1>Average Number of Words Per Text</h1>
      <div className="panel" style={{ height: 400 }}>
        <div className="panel-inner">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart key={chartKey} data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
              <XAxis dataKey="label" tick={{ fill: tickColor }} tickFormatter={(v) => {
                const n = Number(v);
                if (!isNaN(n) && n >= 0 && n <= 23) return formatHourLabel(n);
                return v;
              }} />
              <YAxis tickFormatter={v => roundToTwo(v)} />
              <Tooltip formatter={(value) => [roundToTwo(value), 'Avg words/msg']} contentStyle={{ background: theme === 'light' ? '#ffffff' : '#1f2937', border: 'none' }} />
              <Area
                type="monotone"
                name="Avg words/msg"
                dataKey="value"
                stroke={stroke}
                fill={fill}
                strokeWidth={3}
                dot={false}
                isAnimationActive={true}
                animationBegin={0}
                animationDuration={900}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default WordsPerMessageByHour;
