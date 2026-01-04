import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import fetchData from '../utils/dataFetcher';
import { formatCount } from '../utils/numberFormatter';
import LoadingDots from './LoadingDots';
import MessageBubble from './MessageBubble';

const OverviewTotals = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    const getData = async () => {
      const fetchedData = await fetchData();
      setData(fetchedData);
    };
    getData();
  }, []);

  if (!data) return <LoadingDots />;

  const totalMessages = formatCount(data.total_number_messages ?? data.totalMessages ?? null);
  const totalWords = formatCount(data.total_words_sent ?? data.totalWords ?? null);
  const individualsRaw = data.individualsMessaged ?? data.individuals_messaged ?? data.non_gc_with_min2_msgs ?? (data.conversation_comparison ? data.conversation_comparison.length : null);
  const individuals = formatCount(individualsRaw);

  return (
    <div className="slide">
      <div style={{ width: '60%', maxWidth: 920, margin: '28px auto', display: 'flex', flexDirection: 'column', alignItems: 'stretch', gap: 12, padding: '12px 8px' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: 0, marginBottom: 12 }}>
          <MessageBubble side="right" delay={0} theme="light" contentPadding={6} verticalCenter>
            <div style={{ minWidth: 560, maxWidth: '92vw', textAlign: 'center', fontSize: 28, fontWeight: 900, padding: '4px 8px', lineHeight: 1 }}>{'Your 2025 Messages'}</div>
          </MessageBubble>
        </div>

        <MessageBubble side="left" delay={0.18} theme="light">
          <div style={{ fontSize: 12, fontWeight: 700, opacity: 0.9 }}>Total Messages</div>
          <div style={{ fontSize: 30, fontWeight: 900, marginTop: 8 }}>{totalMessages}</div>
        </MessageBubble>

        <MessageBubble side="right" delay={0.45} theme="light">
          <div style={{ fontSize: 12, fontWeight: 700, opacity: 0.98, color: '#fff' }}>Total Words</div>
          <div style={{ fontSize: 30, fontWeight: 900, marginTop: 8 }}>{totalWords}</div>
        </MessageBubble>

        <MessageBubble side="left" delay={0.75} theme="light">
          <div style={{ fontSize: 12, fontWeight: 700, opacity: 0.9 }}>Individuals Messaged</div>
          <div style={{ fontSize: 30, fontWeight: 900, marginTop: 8 }}>{individuals}</div>
        </MessageBubble>
      </div>
    </div>
  );
};

export default OverviewTotals;
