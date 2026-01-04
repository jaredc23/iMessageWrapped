import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import fetchData from '../utils/dataFetcher';
import { formatCount } from '../utils/numberFormatter';
import MessagesTimelineChart from './MessagesTimelineChartClean';
import LoadingDots from './LoadingDots';

const MessagesSentTimelineSlide = () => {
  const [chartData, setChartData] = useState(null);
  const [chartKey, setChartKey] = useState(0);

  useEffect(() => {
    const getData = async () => {
      const fetchedData = await fetchData();
      if (fetchedData) {
        let labels = [];
        let values = [];
        if (fetchedData.messages_sent_timeline) {
          labels = fetchedData.messages_sent_timeline.dates || [];
          values = fetchedData.messages_sent_timeline.counts || [];
        } else if (fetchedData.messagesTimeline) {
          labels = fetchedData.messagesTimeline.labels || [];
          values = fetchedData.messagesTimeline.values || [];
        }

        if (labels.length && values.length) {
          const formatted = labels.map((label, i) => ({ label, value: values[i] }));
          setChartData(formatted);
          setChartKey(prev => prev + 1);
        } else {
          console.warn('MessagesSentTimelineSlide: no messages timeline data', fetchedData);
        }
      }
    };
    getData();
  }, []);

  if (!chartData) return <LoadingDots />;

  return (
    <div className="slide">
      <h1>Messages Sent Timeline</h1>
      <div className="panel" style={{ height: '400px' }}>
        <div className="panel-inner">
          <MessagesTimelineChart key={chartKey} formatted={chartData} height={400} />
        </div>
      </div>
    </div>
  );
};

export default MessagesSentTimelineSlide;