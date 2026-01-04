import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
import fetchData from '../utils/dataFetcher';
import { formatCount } from '../utils/numberFormatter';
import { ThemeContext } from '../context/ThemeContext';
import LoadingDots from './LoadingDots';

const Top15Emoji = () => {
  const [chartData, setChartData] = useState(null);
  const [chartKey, setChartKey] = useState(0);
  const [topEmoji, setTopEmoji] = useState(null);
  const [topEmojiCount, setTopEmojiCount] = useState(0);
  const { theme } = React.useContext(ThemeContext);
  const colors = theme === 'light'
    ? ['#EF4444', '#2563EB', '#F59E0B', '#0EA5A4', '#7C3AED']
    : ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];

  useEffect(() => {
    const getData = async () => {
      const fetchedData = await fetchData();

      if (fetchedData) {
        const topEmojis = fetchedData.top_emojis_data || fetchedData.topEmojisData || [];
        const emojis = topEmojis[0] || [];
        const counts = topEmojis[1] || [];
        const formatted = emojis.slice(0, 15).map((e, i) => ({ emoji: e, count: counts[i] || 0 }));
        if (formatted.length) {
          setChartData(formatted);
          setTopEmoji(formatted[0].emoji);
          setTopEmojiCount(formatted[0].count || 0);
          setChartKey(prev => prev + 1);
        }
      }
    };
    getData();
  }, []);

  if (!chartData) return <LoadingDots />;

  return (
    <div className="slide">
      <h1>Top Used Emojis</h1>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 16, marginBottom: 12 }}>
          <div style={{ fontSize: 64, lineHeight: 1 }}>{topEmoji || '😊'}</div>
          <div>
            <div style={{ fontSize: 20, fontWeight: 600 }}>Top Emoji</div>
              <div style={{ opacity: 0.85 }}>{formatCount(topEmojiCount)} uses</div>
          </div>
        </div>
      </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6, duration: 0.6 }}>
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ height: '400px', width: '100%', maxWidth: 720, boxSizing: 'border-box', overflow: 'hidden', margin: '0 auto' }} className="panel">
              <div className="panel-inner">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart key={chartKey} data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }} barCategoryGap="20%">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="emoji" tick={{ fill: 'white', fontSize: 14 }} />
                  <YAxis tickFormatter={v => formatCount(v)} />
                  <Tooltip formatter={(value) => [formatCount(value), 'Uses']} contentStyle={{ background: theme === 'light' ? '#ffffff' : '#1f2937', border: 'none' }} />
                  <Bar
                    dataKey="count"
                    name="Uses"
                    fill={colors[0]}
                    radius={[6,6,6,6]}
                    isAnimationActive={true}
                    animationBegin={0}
                    animationDuration={1000}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Top15Emoji;
