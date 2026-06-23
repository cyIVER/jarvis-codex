import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type JarvisCodexPlanProps = {
  title: string;
  subtitle: string;
};

const stages = [
  'Voice or text intent',
  'Episode capture',
  'Memory ledger',
  'Approval ledger',
  'Codex handoff',
  'Bridge-ready lanes',
];

const lanes = [
  'main integration',
  'governance review',
  'plan viewer',
  'runtime gates',
  'video assets',
];

const palette = {
  ink: '#101820',
  paper: '#f4f1e8',
  panel: '#ffffff',
  line: '#25313c',
  teal: '#1f8a84',
  coral: '#d95d39',
  gold: '#e0a526',
  blue: '#3f6f9f',
  muted: '#68727d',
};

const appear = (frame: number, start: number, duration = 18) =>
  interpolate(frame, [start, start + duration], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

const FlowNode: React.FC<{
  label: string;
  index: number;
  active: number;
}> = ({label, index, active}) => {
  const opacity = Math.max(0.28, active);
  const y = interpolate(active, [0, 1], [22, 0]);
  const color = index % 3 === 0 ? palette.teal : index % 3 === 1 ? palette.coral : palette.blue;

  return (
    <div
      style={{
        transform: `translateY(${y}px)`,
        opacity,
        background: palette.panel,
        border: `3px solid ${color}`,
        borderRadius: 8,
        minHeight: 118,
        padding: '24px 26px',
        display: 'flex',
        alignItems: 'center',
        boxShadow: '0 18px 38px rgba(16, 24, 32, 0.14)',
      }}
    >
      <div
        style={{
          width: 38,
          height: 38,
          borderRadius: 19,
          background: color,
          color: palette.panel,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: 18,
          fontSize: 20,
          fontWeight: 800,
        }}
      >
        {index + 1}
      </div>
      <div style={{fontSize: 28, lineHeight: 1.14, fontWeight: 760, color: palette.ink}}>
        {label}
      </div>
    </div>
  );
};

export const JarvisCodexPlan: React.FC<JarvisCodexPlanProps> = ({title, subtitle}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const headline = spring({frame, fps, config: {damping: 120, stiffness: 90}});
  const progress = interpolate(frame, [40, 260], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        background: palette.paper,
        color: palette.ink,
        fontFamily:
          'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(90deg, rgba(16,24,32,0.08) 1px, transparent 1px), linear-gradient(0deg, rgba(16,24,32,0.06) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
        }}
      />
      <div style={{position: 'relative', padding: '72px 86px 62px'}}>
        <header
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 420px',
            columnGap: 54,
            alignItems: 'end',
          }}
        >
          <div style={{transform: `translateY(${interpolate(headline, [0, 1], [20, 0])}px)`}}>
            <div
              style={{
                color: palette.coral,
                fontSize: 26,
                textTransform: 'uppercase',
                fontWeight: 850,
                letterSpacing: 0,
                marginBottom: 14,
              }}
            >
              Animated review asset
            </div>
            <h1 style={{fontSize: 112, lineHeight: 0.95, margin: 0, fontWeight: 900}}>
              {title}
            </h1>
            <p
              style={{
                fontSize: 35,
                lineHeight: 1.22,
                maxWidth: 1120,
                margin: '24px 0 0',
                color: palette.muted,
                fontWeight: 560,
              }}
            >
              {subtitle}
            </p>
          </div>
          <div
            style={{
              background: palette.ink,
              color: palette.paper,
              borderRadius: 8,
              padding: 30,
              minHeight: 178,
              boxShadow: '0 22px 48px rgba(16, 24, 32, 0.22)',
            }}
          >
            <div style={{fontSize: 23, color: palette.gold, fontWeight: 850}}>Safety boundary</div>
            <div style={{fontSize: 34, lineHeight: 1.12, fontWeight: 820, marginTop: 14}}>
              Local state, explicit approvals, no hosted publishing.
            </div>
          </div>
        </header>

        <main
          style={{
            display: 'grid',
            gridTemplateColumns: '1.28fr 0.72fr',
            gap: 42,
            marginTop: 58,
            alignItems: 'start',
          }}
        >
          <section>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 24,
              }}
            >
              {stages.map((stage, index) => {
                const active = appear(frame, 42 + index * 22);
                return <FlowNode key={stage} label={stage} index={index} active={active} />;
              })}
            </div>
            <div
              style={{
                marginTop: 36,
                height: 18,
                background: 'rgba(16,24,32,0.14)',
                borderRadius: 8,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${progress * 100}%`,
                  height: '100%',
                  background: `linear-gradient(90deg, ${palette.teal}, ${palette.gold}, ${palette.coral})`,
                }}
              />
            </div>
          </section>

          <aside
            style={{
              background: palette.panel,
              border: `3px solid ${palette.line}`,
              borderRadius: 8,
              padding: '34px 34px 28px',
              boxShadow: '0 18px 38px rgba(16, 24, 32, 0.12)',
            }}
          >
            <h2 style={{fontSize: 42, lineHeight: 1, margin: 0, fontWeight: 880}}>Planning lanes</h2>
            <div style={{display: 'grid', gap: 16, marginTop: 28}}>
              {lanes.map((lane, index) => {
                const active = appear(frame, 92 + index * 18);
                return (
                  <div
                    key={lane}
                    style={{
                      opacity: active,
                      transform: `translateX(${interpolate(active, [0, 1], [24, 0])}px)`,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      padding: '16px 0',
                      borderTop: index === 0 ? '0' : '2px solid rgba(16,24,32,0.1)',
                    }}
                  >
                    <div
                      style={{
                        width: 16,
                        height: 16,
                        borderRadius: 8,
                        background:
                          index % 2 === 0 ? palette.teal : index % 3 === 0 ? palette.gold : palette.coral,
                      }}
                    />
                    <div style={{fontSize: 29, fontWeight: 780}}>{lane}</div>
                  </div>
                );
              })}
            </div>
          </aside>
        </main>
      </div>
    </AbsoluteFill>
  );
};
