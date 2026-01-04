import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import fetchData from '../utils/dataFetcher';
import { formatMinutesOrSeconds } from '../utils/numberFormatter';
import LoadingDots from './LoadingDots';

const SlowestResponseNonGroup = () => {
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
  if (data.top_bottom_n_non_gc_by_response_time && data.top_bottom_n_non_gc_by_response_time.bottom) {
    list = data.top_bottom_n_non_gc_by_response_time.bottom.map(item => ({ name: item[0], responseTime: item[1] }));
  } else if (data.conversation_comparison) {
    list = data.conversation_comparison.filter(c => !c.is_group_chat).sort((a,b) => (b.median_response_time_minutes||0)-(a.median_response_time_minutes||0)).slice(0,10).map(c => ({ name: c.name, responseTime: c.median_response_time_minutes }));
  }

  return (
    <div className="slide">
      <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1 }}>
        Fastest Non-Group Chats by Response Time
      </motion.h1>
      <ul>
        {list.map((chat, index) => (
          <motion.li key={index} initial={{ opacity: 0, x: -50 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: index * 0.3 }}>
            {chat.name}: {typeof chat.responseTime === 'number' ? formatMinutesOrSeconds(chat.responseTime) : (chat.responseTime ?? '—')}
          </motion.li>
        ))}
      </ul>
    </div>
  );
};

export default SlowestResponseNonGroup;
