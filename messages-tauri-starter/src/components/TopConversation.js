import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import fetchData from '../utils/dataFetcher';
import { formatCount, formatMinutesOrSeconds } from '../utils/numberFormatter';
import LoadingDots from './LoadingDots';
import MessageBubble from './MessageBubble';

const TopConversation = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    const getData = async () => {
      const fetchedData = await fetchData();
      setData(fetchedData);
    };
    getData();
  }, []);

  if (!data) return <LoadingDots />;
  let topConversation = null;
  if (data.top_n_chats_by_messages && data.top_n_chats_by_messages.length) {
    const name = data.top_n_chats_by_messages[0][0];
    const conv = (data.conversation_comparison || []).find(c => c.name === name);
    topConversation = conv || { name, messages: data.top_n_chats_by_messages[0][1] };
  } else if (data.topConversation) {
    topConversation = data.topConversation;
  } else if (data.conversation_comparison && data.conversation_comparison.length) {
    topConversation = data.conversation_comparison.slice().sort((a,b) => (b.total_messages||0)-(a.total_messages||0))[0];
  }

  const name = topConversation?.name ?? '—';
  // determine messages you sent (prefer explicit field, fall back to top_n list)
  const topNMap = (data?.top_n_chats_by_messages || []).reduce((acc, item) => { acc[item[0]] = item[1]; return acc; }, {});
  const youSentRaw = topConversation?.messages_sent_you ?? topConversation?.messagesSentYou ?? topNMap[name] ?? topConversation?.messages ?? null;
  const totalRaw = topConversation?.total_messages ?? topConversation?.messages ?? null;
  const youSent = formatCount(youSentRaw);
  const totalMessages = formatCount(totalRaw);
  const words = (() => {
    const conv = topConversation || {};
    const totalWords = conv.total_words ?? conv.totalWords ?? conv.words;
    if (typeof totalWords === 'number') return totalWords;
    const avg = conv.avg_words_per_message ?? conv.avgWordsPerMessage ?? conv.avg_words;
    const msgs = conv.total_messages ?? conv.messages;
    if (typeof avg === 'number' && typeof msgs === 'number') return Math.round(avg * msgs);
    if (typeof avg === 'number') return `${avg} avg`;
    return '—';
  })();
  const responseTime = topConversation?.responseTime ?? topConversation?.median_response_time_minutes ?? '—';

  return (
    <div className="slide">
      <div style={{ width: '68%', maxWidth: 920, margin: '20px auto', display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
          <MessageBubble side="left" delay={0} theme="light" contentPadding={6} verticalCenter>
            <div style={{ minWidth: 520, textAlign: 'center', fontSize: 48, fontWeight: 900, padding: '6px 10px' }}>Top Conversation</div>
          </MessageBubble>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
          <MessageBubble side="right" delay={0.25} theme="light">
            <div style={{ minWidth: 560, textAlign: 'center', fontSize: 24, fontWeight: 900 }}>{name}</div>
            <div style={{ marginTop: 8, fontSize: 14, fontWeight: 700, textAlign: 'center' }}>Messages Sent By You: {youSent}</div>
            <div style={{ marginTop: 6, fontSize: 14, fontWeight: 700, textAlign: 'center' }}>Total Messages: {totalMessages}</div>
            <div style={{ marginTop: 6, fontSize: 14, fontWeight: 700, textAlign: 'center' }}>Words: {typeof words === 'number' ? formatCount(words) : words}</div>
            <div style={{ marginTop: 6, fontSize: 14, fontWeight: 700, textAlign: 'center' }}>Your Average Response Time: {typeof responseTime === 'number' ? formatMinutesOrSeconds(responseTime) : responseTime}</div>
          </MessageBubble>
        </div>
      </div>
    </div>
  );
};

export default TopConversation;
