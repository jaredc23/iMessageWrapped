import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import fetchData from '../utils/dataFetcher';
import { formatCount } from '../utils/numberFormatter';
import LoadingDots from './LoadingDots';
import MessageBubble from './MessageBubble';

const TopConversations = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    const getData = async () => {
      const fetchedData = await fetchData();
      setData(fetchedData);
    };
    getData();
  }, []);

  if (!data) return <LoadingDots />;
  let topConversations = [];
  if (data.top_n_chats_by_messages) {
    const names = data.top_n_chats_by_messages.map(item => item[0]);
    topConversations = names.map((name) => {
      const conv = (data.conversation_comparison || []).find(c => c.name === name);
      return conv || { name };
    });
  } else if (data.topConversations) {
    topConversations = data.topConversations;
  } else if (data.conversation_comparison) {
    topConversations = data.conversation_comparison.slice().sort((a,b) => (b.total_messages||0)-(a.total_messages||0)).slice(0,10);
  }

  // Build a lookup for messages-you-sent from the provided top_n list (fallback)
  const topNMap = (data.top_n_chats_by_messages || []).reduce((acc, item) => {
    acc[item[0]] = item[1];
    return acc;
  }, {});

  const shownNames = topConversations.map(c => c.name);
  const otherConversations = (data.conversation_comparison || []).filter(c => !shownNames.includes(c.name)).slice(0, 5);
  const topCount = Math.min(6, topConversations.length);

  return (
    <div className="slide">
      <div style={{ width: '76%', maxWidth: 980, margin: '8px auto 0', display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'stretch' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: 0 }}>
          <div style={{
            display: 'inline-flex',
            flexDirection: 'column',
            alignItems: 'center',
            background: '#0b93f6',
            color: 'white',
            padding: '6px 12px',
            borderRadius: 9999,
            minWidth: 240,
            boxShadow: '0 1px 0 rgba(0,0,0,0.06)'
          }}>
            <div style={{ textAlign: 'center', fontSize: 20, fontWeight: 900, lineHeight: 1 }}>{'Top Conversations'}</div>
            <div style={{ textAlign: 'center', fontSize: 13, fontWeight: 700, marginTop: 4 }}>{'By Number of Sent Msgs'}</div>
          </div>
        </div>

        <div style={{ marginTop: 12 }}>
        {topConversations.slice(0, topCount).map((conversation, index) => {
          const overallIndex = index;
          const side = (overallIndex % 2 === 0) ? 'left' : 'right';
          const delay = 0.2 + overallIndex * 0.18;
          return (
            <MessageBubble key={conversation.name || `top-${index}`} side={side} delay={delay} theme="light" contentPadding={8}>
              <div style={{ fontSize: 13, fontWeight: 800 }}>{conversation.name}</div>
              <div style={{ marginTop: 6, fontSize: 11 }}>You Sent: {formatCount(conversation.messages_sent_you ?? conversation.messagesSentYou ?? topNMap[conversation.name] ?? null)}</div>
              <div style={{ marginTop: 4, fontSize: 11 }}>Total Messages: {formatCount(conversation.total_messages ?? conversation.messages ?? null)}</div>
              
            </MessageBubble>
          );
        })}
        </div>

        <div style={{ marginTop: 6 }}>
          {otherConversations && otherConversations.length ? otherConversations.map((conversation, idx) => {
              // force the bottom list to start on the right, then alternate: right, left, right...
              const side = (idx % 2 === 0) ? 'right' : 'left';
              const overallIndex = topCount + idx;
              const delay = 0.2 + overallIndex * 0.18; // continuous increasing delay across both lists
              return (
              <MessageBubble key={conversation.name || `other-${idx}`} side={side} delay={delay} theme="light" contentPadding={8}>
                <div style={{ fontSize: 11, fontWeight: 700 }}>{conversation.name}</div>
                  <div style={{ marginTop: 6, fontSize: 10 }}>Total Messages: {formatCount(conversation.total_messages ?? conversation.messages ?? null)}</div>
              </MessageBubble>
            );
          }) : (
            <p style={{ opacity: 0.8 }}>No additional conversations available.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TopConversations;
