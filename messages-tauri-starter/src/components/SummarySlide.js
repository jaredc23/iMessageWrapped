import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import fetchData from '../utils/dataFetcher';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatCount, formatMinutesOrSeconds } from '../utils/numberFormatter';
import MessagesTimelineChart from './MessagesTimelineChartClean';
import LoadingDots from './LoadingDots';

const SummarySlide = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    const getData = async () => {
      const fetchedData = await fetchData();
      setData(fetchedData);
    };
    getData();
  }, []);

  if (!data) return <LoadingDots />;
  // Map values from snake_case JSON
  const totalMessages = formatCount(data.total_number_messages ?? data.totalMessages ?? null);
  const totalWords = formatCount(data.total_words_sent ?? data.totalWords ?? null);
  const topEmoji = data.top_emojis_data ? data.top_emojis_data[0]?.[0] : (data.topEmoji ?? data.top_emoji ?? '—');
  // determine top conversation (name)
  let topConversation = null;
  if (data.top_n_chats_by_messages && data.top_n_chats_by_messages.length) {
    topConversation = data.top_n_chats_by_messages[0][0];
  } else if (data.top_n_chats_by_messages_sent && data.top_n_chats_by_messages_sent.length) {
    topConversation = data.top_n_chats_by_messages_sent[0][0];
  } else if (data.topConversation) {
    topConversation = data.topConversation.name ?? data.topConversation;
  } else if (data.conversation_comparison && data.conversation_comparison.length) {
    const tc = data.conversation_comparison.slice().sort((a,b) => (b.total_messages||0)-(a.total_messages||0))[0];
    topConversation = tc?.name ?? null;
  }

  let avgResponseRaw = null;
  if (data.response_time_by_hour && data.response_time_by_hour.avg_minutes) {
    const vals = data.response_time_by_hour.avg_minutes;
    avgResponseRaw = vals.reduce((a,b)=>a+b,0)/vals.length;
  } else if (data.responseTimeByHour && data.responseTimeByHour.values) {
    const vals = data.responseTimeByHour.values;
    avgResponseRaw = vals.reduce((a,b)=>a+b,0)/vals.length;
  }

  return (
    <div className="slide">
      <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1 }}>
        iMessages Wrapped 2025
      </motion.h1>
      {(() => {
        const items = [
          { text: `Total Messages: ${totalMessages}`, delay: 0.5 },
          { text: `Total Words: ${totalWords}`, delay: 1 },
          { text: `Top Conversation: ${topConversation ?? '—'}`, delay: 1.5 },
          { text: `Top Emoji: ${topEmoji}`, delay: 2.0 },
          { text: `Average Response Time: ${avgResponseRaw !== null ? formatMinutesOrSeconds(avgResponseRaw) : '—'}`, delay: 2.5 }
        ];

        return items.map((it, idx) => {
          const isLeft = idx % 2 === 0;
          const leftLight = '#e5e5ea';
          const rightLight = '#0b93f6';
          const rightDark = '#0a84ff';
          const prefersDark = (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
          // Always use the light-gray for left badges so they match the left message bubbles
          const bg = isLeft ? leftLight : (prefersDark ? rightDark : rightLight);
          const color = isLeft ? '#000' : '#fff';
          return (
            <motion.div key={idx} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.9, delay: it.delay }} style={{ width: '100%', display: 'flex', justifyContent: 'center', margin: '8px 0' }}>
              <div style={{ display: 'inline-block', padding: '6px 12px', borderRadius: 999, background: bg, color, fontWeight: 700, textAlign: 'center' }}>
                {it.text}
              </div>
            </motion.div>
          );
        });
      })()}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1, delay: 3.0 }}>
        <h2>Message Activity</h2>
        {(() => {
          const labels = data.messages_sent_timeline?.dates || data.messagesTimeline?.labels || [];
          const values = data.messages_sent_timeline?.counts || data.messagesTimeline?.values || [];
          if (!labels || !labels.length || !values || !values.length) return <p>No timeline data available.</p>;
          const formatted = labels.map((label, i) => ({ label, value: values[i] ?? 0 }));
          return (
            <div style={{ height: 300, width: '100%' }} className="panel">
              <div className="panel-inner" style={{ height: '100%' }}>
                <MessagesTimelineChart formatted={formatted} height={300} />
              </div>
            </div>
          );
        })()}
      </motion.div>
    </div>
  );
};

export default SummarySlide;