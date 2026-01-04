import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import fetchData from '../utils/dataFetcher';
import { formatCount } from '../utils/numberFormatter';
import LoadingDots from './LoadingDots';

const IndividualsMessaged = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    const getData = async () => {
      const fetchedData = await fetchData();
      setData(fetchedData);
    };
    getData();
  }, []);
  if (!data) return <LoadingDots />;
  const individualsRaw = data.individualsMessaged ?? data.individuals_messaged ?? data.non_gc_with_min2_msgs ?? (data.conversation_comparison ? data.conversation_comparison.length : null);
  const individuals = formatCount(individualsRaw);

  return (
    <div className="slide">
      <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1 }}>
        Individuals Messaged: {individuals}
      </motion.h1>
    </div>
  );
};

// REMOVED: unused slide component
// This file was neutralized to avoid keeping unused Slide components in the build.
export default null;
