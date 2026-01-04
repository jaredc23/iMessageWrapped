import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import fetchData from '../utils/dataFetcher';
import { formatMinutesOrSeconds, formatHourLabel } from '../utils/numberFormatter';
import { ThemeContext } from '../context/ThemeContext';
import LoadingDots from './LoadingDots';

const ResponseTimeByHour = () => {
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    const getData = async () => {
      const fetchedData = await fetchData();
      if (fetchedData) {
        let labels = [];
        let values = [];
        if (fetchedData.response_time_by_hour) {
          labels = fetchedData.response_time_by_hour.hours || [];
          values = fetchedData.response_time_by_hour.avg_minutes || [];
        } else if (fetchedData.responseTimeByHour) {
          labels = fetchedData.responseTimeByHour.labels || [];
          values = fetchedData.responseTimeByHour.values || [];
        }

        if (labels.length && values.length) {
          const formatted = labels.map((label, i) => ({ label, value: values[i] }));
          setChartData(formatted);
        } else {
          console.warn('ResponseTimeByHour: no response time by hour data', fetchedData);
        }
      }
    };
    getData();
  }, []);

  if (!chartData) return <LoadingDots />;

  const { theme } = React.useContext(ThemeContext);
  const stroke = theme === 'light' ? '#10B981' : '#34D399';
  const gridStroke = theme === 'light' ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.06)';
  const tickColor = theme === 'light' ? '#000000' : '#ffffff';

  return (
    <div className="slide">
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ margin: 0 }}>Average Response Time</h1>
        <div style={{ marginTop: 6, fontSize: 14, fontWeight: 600 }}>(Based On The Time Received)</div>
      </div>
      <div className="panel" style={{ height: '400px' }}>
        <div className="panel-inner">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
              <XAxis dataKey="label" tick={{ fill: tickColor }} tickFormatter={(v) => {
                const n = Number(v);
                if (!isNaN(n) && n >= 0 && n <= 23) return formatHourLabel(n);
                return v;
              }} />
              <YAxis tickFormatter={v => formatMinutesOrSeconds(v)} />
              <Tooltip formatter={(value) => [formatMinutesOrSeconds(value), 'Response Time']} contentStyle={{ background: theme === 'light' ? '#ffffff' : '#1f2937', border: 'none' }} />
              <Line type="monotone" name="Response Time" dataKey="value" stroke={stroke} dot={false} strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default ResponseTimeByHour;
