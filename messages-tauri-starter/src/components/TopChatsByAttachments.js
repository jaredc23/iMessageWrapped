import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import fetchData from '../utils/dataFetcher';
import { formatCount } from '../utils/numberFormatter';
import LoadingDots from './LoadingDots';
import MessageBubble from './MessageBubble';

const TopChatsByAttachments = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    const getData = async () => {
      const fetchedData = await fetchData();
      setData(fetchedData);
    };
    getData();
  }, []);

  if (!data) return <LoadingDots />;
  let list = [];
  if (data.top_n_chats_by_attachments) {
    list = data.top_n_chats_by_attachments.map(item => ({ name: item[0], attachments: item[1] }));
  } else if (data.topChatsByAttachments) {
    list = data.topChatsByAttachments;
  } else if (data.conversation_comparison) {
    list = data.conversation_comparison.slice().sort((a,b) => (b.total_attachments||0)-(a.total_attachments||0)).slice(0,10).map(c => ({ name: c.name, attachments: c.total_attachments }));
  }

  return (
    <div className="slide">
      <div style={{ width: '68%', maxWidth: 920, margin: '20px auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <MessageBubble side="right" delay={0} theme="light" contentPadding={6} verticalCenter>
            <div style={{ minWidth: 520, textAlign: 'center', fontSize: 28, fontWeight: 900, padding: '4px 8px' }}>Top Chats by Attachments</div>
          </MessageBubble>
        </div>

        {list.map((chat, index) => {
          const side = (index % 2 === 0) ? 'left' : 'right';
          const delay = 0.15 + index * 0.14;
          return (
            <div key={chat.name || index} style={{ display: 'flex', justifyContent: side === 'left' ? 'flex-start' : 'flex-end' }}>
              <MessageBubble side={side} delay={delay} theme="light" contentPadding={8}>
                <div style={{ fontSize: 14, fontWeight: 800 }}>{chat.name}</div>
                <div style={{ marginTop: 6, fontSize: 13 }}>Attachments: {formatCount(chat.attachments ?? 0)}</div>
              </MessageBubble>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TopChatsByAttachments;
