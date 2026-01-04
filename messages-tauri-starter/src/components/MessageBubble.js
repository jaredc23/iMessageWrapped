import React, { useRef, useState, useLayoutEffect, useEffect } from 'react';
import { motion } from 'framer-motion';

const containerStyle = { display: 'flex', flexDirection: 'column' };
const wrapperStyleBase = { position: 'relative', display: 'flex', width: '100%' };
const DEFAULT_CONTENT_PADDING = { top: 20, right: 24, bottom: 20, left: 24 };

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

// New clean MessageBubble implementation: single continuous SVG path for rounded rect + tail.
const MessageBubble = ({ side = 'left', children, delay = 0, theme = 'auto', contentPadding: contentPaddingProp, verticalCenter = false }) => {
  const isLeft = side === 'left';

  // detect OS/browser dark mode and update colors to match iMessage night mode
  const systemPrefersDark = (typeof window !== 'undefined' && window.matchMedia) ? window.matchMedia('(prefers-color-scheme: dark)').matches : false;
  const [prefersDark, setPrefersDark] = useState(
    theme === 'auto' ? systemPrefersDark : (theme === 'dark')
  );

  useEffect(() => {
    if (theme !== 'auto') return; // only listen when auto
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handle = (e) => setPrefersDark(e.matches);
    // update initial state in case it changed between render and effect
    setPrefersDark(mq.matches);
    if (mq.addEventListener) mq.addEventListener('change', handle); else mq.addListener(handle);
    return () => { if (mq.removeEventListener) mq.removeEventListener('change', handle); else mq.removeListener(handle); };
  }, [theme]);

  let fill, textColor;
  if (isLeft) {
    // left bubble: light gray in light mode, dark gray in dark mode (iMessage style)
    fill = prefersDark ? '#2C2C2E' : '#e5e5ea';
    textColor = prefersDark ? '#ffffff' : '#000000';
  } else {
    // right bubble: blue in light mode, slightly adjusted blue for dark mode
    fill = prefersDark ? '#0a84ff' : '#0b93f6';
    textColor = '#ffffff';
  }

  const wrapperRef = useRef(null);
  const [dims, setDims] = useState({ width: 160, height: 64 });
  const [containerW, setContainerW] = useState(1000);

  useLayoutEffect(() => {
    const el = wrapperRef.current;
    if (!el) return;
    // normalize content padding: allow number or object
    const pad = (contentPaddingProp != null)
      ? (typeof contentPaddingProp === 'number'
          ? { top: contentPaddingProp, right: contentPaddingProp, bottom: contentPaddingProp, left: contentPaddingProp }
          : { top: contentPaddingProp.top ?? DEFAULT_CONTENT_PADDING.top, right: contentPaddingProp.right ?? DEFAULT_CONTENT_PADDING.right, bottom: contentPaddingProp.bottom ?? DEFAULT_CONTENT_PADDING.bottom, left: contentPaddingProp.left ?? DEFAULT_CONTENT_PADDING.left }
        )
      : DEFAULT_CONTENT_PADDING;

    const ro = new ResizeObserver(entries => {
      for (const e of entries) {
        const rect = e.contentRect;
        setDims({ width: Math.max(120, rect.width + pad.left + pad.right), height: Math.max(48, rect.height + pad.top + pad.bottom) });
      }
    });
    ro.observe(el);

    // also observe the parent container width so we can cap bubble size and avoid overflow
    const parent = el.parentElement;
    if (parent) {
      const ro2 = new ResizeObserver(entries => {
        for (const e of entries) {
          const rect = e.contentRect;
          setContainerW(rect.width || Math.max(320, window.innerWidth * 0.6));
        }
      });
      ro2.observe(parent);
      const parentRect = parent.getBoundingClientRect();
      setContainerW(parentRect.width || Math.max(320, window.innerWidth * 0.6));

      const rect = el.getBoundingClientRect();
      setDims({ width: Math.max(120, rect.width + pad.left + pad.right), height: Math.max(48, rect.height + pad.top + pad.bottom) });

      return () => { ro.disconnect(); ro2.disconnect(); };
    }

    const rect = el.getBoundingClientRect();
    setDims({ width: Math.max(120, rect.width + pad.left + pad.right), height: Math.max(48, rect.height + pad.top + pad.bottom) });
    return () => ro.disconnect();
  }, []);

  // bubble geometry
  // reduce extra vertical buffer so bubbles don't have excessive bottom padding
  const baseH = Math.max(40, dims.height + 2);
  const r = clamp(Math.floor(baseH * 0.22), 8, 28);

  // tail geometry (depends on baseH)
  const tailDepth = clamp(Math.floor(baseH * 0.28), 10, 44);
  const tailHeight = clamp(Math.floor(baseH * 0.18), 10, 48);
  const tailCenterY = baseH - Math.floor(r / 2) - 2;
  const tailTopY = tailCenterY - Math.floor(tailHeight / 2);
  const tailBottomY = tailCenterY + Math.floor(tailHeight / 2);

  // base bubble width (content-driven). Use measured content width; do not wrap — bubble grows to fit text.
  const desiredBaseW = Math.max(120, dims.width + 6);
  const baseW = desiredBaseW;

  // SVG sizing: include space for tail on left or right
  const svgWidth = baseW + tailDepth;
  const bubbleOffsetX = isLeft ? tailDepth : 0; // shift bubble right when left tail

  // helper: compute anchor point on bottom corner arc given y
  const arcAnchor = (cornerCenterX, cornerCenterY, radius, y, sideSign) => {
    const dy = y - cornerCenterY;
    if (Math.abs(dy) >= radius) return { x: sideSign > 0 ? cornerCenterX + radius : cornerCenterX - radius, y };
    const dx = Math.sqrt(Math.max(0, radius * radius - dy * dy));
    const x = sideSign > 0 ? cornerCenterX + dx : cornerCenterX - dx;
    // tangent vector at that point = (-dy, dx) (not normalized)
    let tx = -dy;
    let ty = dx * (sideSign > 0 ? 1 : -1);
    const len = Math.hypot(tx, ty) || 1;
    tx /= len; ty /= len;
    return { x, y, tx, ty };
  };
 
  // Build the left-oriented bubble+tail path. We'll mirror this with an SVG transform for the right-side bubble
  const buildPath = () => {
    const bubbleX = bubbleOffsetX;
    const bubbleY = 0;
    const bubbleW = baseW;
    const bubbleH = baseH;

    const bottomLeftCenter = { x: bubbleX + r, y: bubbleY + bubbleH - r };

    // place tip inset a bit from the extreme so it's thicker and overlaps the corner
    const tipInset = Math.max(8, Math.floor(tailDepth * 0.3));
    const tipX = bubbleX - tipInset; // left-oriented tip
    const tipY = tailCenterY;

    // anchors on bottom-left rounded corner
    const bottomAnchor = arcAnchor(bottomLeftCenter.x, bottomLeftCenter.y, r, tailBottomY, -1);
    const topAnchor = arcAnchor(bottomLeftCenter.x, bottomLeftCenter.y, r, tailTopY, -1);

    // control handle distances and slight overlap so tail covers rounded corner seam
    const k = Math.max(5, Math.floor(r * 0.28));
    const approach = 0.36; // larger -> blunter, wider tip
    const overlap = Math.max(3, Math.floor(r * 0.18));

    // nudge anchors inward slightly so tail overlaps the rounded corner (remove visual gap)
    bottomAnchor.x -= overlap;
    topAnchor.x -= overlap;

    // additional tiny downward nudge on the top anchor to close the opposite corner seam
    topAnchor.y += Math.max(2, Math.floor(r * 0.06));

    const c1 = { x: bottomAnchor.x + bottomAnchor.tx * k, y: bottomAnchor.y + bottomAnchor.ty * k };
    const c4 = { x: topAnchor.x + topAnchor.tx * k, y: topAnchor.y + topAnchor.ty * k };

    const c2 = { x: tipX + (bottomAnchor.x - tipX) * approach, y: tipY - Math.max(4, Math.floor(tailHeight * 0.18)) };
    const c3 = { x: tipX + (topAnchor.x - tipX) * approach, y: tipY + Math.max(4, Math.floor(tailHeight * 0.18)) };

    return [
      `M ${bubbleX + r} ${bubbleY}`,
      `H ${bubbleX + bubbleW - r}`,
      `A ${r} ${r} 0 0 1 ${bubbleX + bubbleW} ${bubbleY + r}`,
      `V ${bubbleY + bubbleH - r}`,
      `A ${r} ${r} 0 0 1 ${bubbleX + bubbleW - r} ${bubbleY + bubbleH}`,
      `H ${bubbleX + r}`,
      `A ${r} ${r} 0 0 1 ${bubbleX} ${bubbleY + bubbleH - r}`,
      `L ${bottomAnchor.x} ${bottomAnchor.y}`,
      `C ${c1.x} ${c1.y} ${c2.x} ${c2.y} ${tipX} ${tipY}`,
      `C ${c3.x} ${c3.y} ${c4.x} ${c4.y} ${topAnchor.x} ${topAnchor.y}`,
      `L ${bubbleX} ${bubbleY + r}`,
      `A ${r} ${r} 0 0 1 ${bubbleX + r} ${bubbleY}`,
      `Z`
    ].join(' ');
  };

  const path = buildPath();
  const pathTransform = isLeft ? undefined : `translate(${svgWidth}) scale(-1,1)`;

  const wrapperStyle = { ...wrapperStyleBase, justifyContent: isLeft ? 'flex-start' : 'flex-end' };
  const entryY = (typeof window !== 'undefined') ? Math.max(240, Math.min(window.innerHeight * 0.7, 900)) : 360;

  return (
    <div style={containerStyle}>
      <div style={wrapperStyle}>
          <motion.div
            initial={{ opacity: 0, y: entryY, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: 'spring', stiffness: 90, damping: 14, mass: 0.6, delay }}
            style={{ position: 'relative', minWidth: 160, display: 'inline-block', overflow: 'visible', maxWidth: '100%', boxSizing: 'border-box' }}
          >
            <svg
            width={svgWidth}
            height={baseH}
            viewBox={`0 0 ${svgWidth} ${baseH}`}
            style={{ position: 'absolute', left: (isLeft ? 0 : 'auto'), right: (isLeft ? 'auto' : 0), top: 0, zIndex: 0, pointerEvents: 'none', overflow: 'visible' }}
            preserveAspectRatio="xMinYMin meet"
          >
            <path d={path} fill={fill} transform={pathTransform} />
          </svg>

          <div
            ref={wrapperRef}
            style={{
              position: 'relative',
              zIndex: 2,
              padding: `${(contentPaddingProp != null ? (typeof contentPaddingProp === 'number' ? contentPaddingProp : (contentPaddingProp.top ?? DEFAULT_CONTENT_PADDING.top)) : DEFAULT_CONTENT_PADDING.top)}px ${(contentPaddingProp != null ? (typeof contentPaddingProp === 'number' ? contentPaddingProp : (contentPaddingProp.right ?? DEFAULT_CONTENT_PADDING.right)) : DEFAULT_CONTENT_PADDING.right)}px ${(contentPaddingProp != null ? (typeof contentPaddingProp === 'number' ? contentPaddingProp : (contentPaddingProp.bottom ?? DEFAULT_CONTENT_PADDING.bottom)) : DEFAULT_CONTENT_PADDING.bottom)}px ${(contentPaddingProp != null ? (typeof contentPaddingProp === 'number' ? contentPaddingProp : (contentPaddingProp.left ?? DEFAULT_CONTENT_PADDING.left)) : DEFAULT_CONTENT_PADDING.left)}px`,
              color: textColor,
              transform: `translateX(${bubbleOffsetX}px)`,
              display: verticalCenter ? 'flex' : undefined,
              alignItems: verticalCenter ? 'center' : undefined,
              justifyContent: verticalCenter ? 'center' : undefined
            }}
          >
            {children}
          </div>
        </motion.div>
      </div>
    </div>
  );
};



export default MessageBubble;
