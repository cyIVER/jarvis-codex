import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const palette = {
  void: '#070a0d',
  panel: '#10151a',
  panel2: '#161116',
  line: '#31424a',
  cyan: '#39d6e8',
  amber: '#f0b840',
  red: '#d94d3d',
  green: '#55d68a',
  text: '#f3f7f8',
  muted: '#a9bac0',
};

const completed = [
  'Project-local Codex governance and validator',
  'Doctor opt-in governance summary',
  'Voice path with approved local STT controls',
  'Runtime HUD, PTY, approvals, PWA, and mobile readiness',
  'Release gates, evidence ledger, and operator briefs',
  'Bounded loop run, schedule, policy, and evidence brief',
];

const left = [
  'Actual iPhone private-network validation evidence',
  'Approved Gemini Live network validation',
  'Signed Electron package and publication review',
  'Accepted external security reviewer attestation',
  'Operator decision on unattended or background scheduling',
  'Future AG adversary panes and release publication path',
];

const decisions = [
  'Which release gate gets human evidence first?',
  'What cloud voice spend and credential scope is acceptable?',
  'Who signs off external security findings?',
  'Should generated Remotion assets remain local or ship?',
  'Is any background automation allowed beyond foreground loops?',
];

const phases = [
  {label: 'Governance', value: '156 checks'},
  {label: 'Loop', value: '25 checks'},
  {label: 'Tests', value: '325 passing'},
  {label: 'Safety', value: 'gated'},
];

const fade = (frame: number, start: number, duration = 24) =>
  interpolate(frame, [start, start + duration], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const scan = (frame: number, start: number) =>
  interpolate(frame, [start, start + 90], [-120, 980], {
    easing: Easing.inOut(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const HudShell: React.FC<{children: React.ReactNode; label: string}> = ({children, label}) => {
  const frame = useCurrentFrame();
  const pulse = interpolate(Math.sin(frame / 14), [-1, 1], [0.42, 0.82]);

  return (
    <AbsoluteFill
      style={{
        background: palette.void,
        color: palette.text,
        fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(90deg, rgba(57,214,232,0.1) 1px, transparent 1px), linear-gradient(0deg, rgba(240,184,64,0.08) 1px, transparent 1px)',
          backgroundSize: '96px 96px',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 42,
          border: `2px solid rgba(57,214,232,${pulse})`,
          boxShadow: 'inset 0 0 42px rgba(57,214,232,0.14), 0 0 42px rgba(57,214,232,0.12)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 82,
          top: 64,
          color: palette.amber,
          fontSize: 25,
          fontWeight: 800,
          textTransform: 'uppercase',
        }}
      >
        {label}
      </div>
      <div
        style={{
          position: 'absolute',
          right: 82,
          top: 64,
          color: palette.cyan,
          fontSize: 25,
          fontWeight: 800,
          textTransform: 'uppercase',
        }}
      >
        08:00 EST
      </div>
      {children}
    </AbsoluteFill>
  );
};

const Metric: React.FC<{label: string; value: string; index: number}> = ({label, value, index}) => {
  const frame = useCurrentFrame();
  const active = fade(frame, 28 + index * 10);
  return (
    <div
      style={{
        opacity: active,
        transform: `translateY(${interpolate(active, [0, 1], [28, 0])}px)`,
        border: `2px solid ${palette.line}`,
        background: index % 2 === 0 ? palette.panel : palette.panel2,
        padding: '24px 26px',
        minHeight: 132,
      }}
    >
      <div style={{fontSize: 24, color: palette.muted, fontWeight: 700, textTransform: 'uppercase'}}>{label}</div>
      <div style={{fontSize: 52, color: index === 3 ? palette.green : palette.cyan, fontWeight: 900, marginTop: 10}}>
        {value}
      </div>
    </div>
  );
};

const BulletList: React.FC<{items: string[]; start: number; color: string}> = ({items, start, color}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: 'grid', gap: 18}}>
      {items.map((item, index) => {
        const active = fade(frame, start + index * 9);
        return (
          <div
            key={item}
            style={{
              opacity: active,
              transform: `translateX(${interpolate(active, [0, 1], [38, 0])}px)`,
              display: 'grid',
              gridTemplateColumns: '28px 1fr',
              gap: 16,
              alignItems: 'start',
              fontSize: 31,
              lineHeight: 1.18,
              color: palette.text,
            }}
          >
            <div style={{width: 18, height: 18, marginTop: 9, background: color}} />
            <span>{item}</span>
          </div>
        );
      })}
    </div>
  );
};

const TitleSlide: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const title = spring({frame, fps, config: {damping: 120, stiffness: 90}});
  const lineY = scan(frame, 36);

  return (
    <HudShell label="Jarvis Codex night cycle">
      <div style={{position: 'absolute', left: 120, top: 168, width: 1220}}>
        <div
          style={{
            color: palette.red,
            fontSize: 31,
            fontWeight: 850,
            textTransform: 'uppercase',
            opacity: fade(frame, 8),
          }}
        >
          Overnight platform report
        </div>
        <h1
          style={{
            fontSize: 94,
            lineHeight: 0.96,
            margin: '24px 0 0',
            fontWeight: 950,
            transform: `translateY(${interpolate(title, [0, 1], [40, 0])}px)`,
          }}
        >
          What changed, what remains, and what needs your call.
        </h1>
        <p
          style={{
            fontSize: 31,
            lineHeight: 1.24,
            color: palette.muted,
            marginTop: 28,
            maxWidth: 1080,
            opacity: fade(frame, 28),
          }}
        >
          Codex and Antigravity stayed inside governed local boundaries: evidence first, execution gated, release gates open until a human accepts proof.
        </p>
      </div>
      <div style={{position: 'absolute', left: 120, right: 120, bottom: 82, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 22}}>
        {phases.map((metric, index) => (
          <Metric key={metric.label} {...metric} index={index} />
        ))}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 52,
          top: lineY,
          width: 1816,
          height: 4,
          background: palette.cyan,
          opacity: 0.46,
        }}
      />
    </HudShell>
  );
};

const CompletedSlide: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <HudShell label="Completed surfaces">
      <div style={{position: 'absolute', left: 112, top: 154, right: 112, display: 'grid', gridTemplateColumns: '0.86fr 1.14fr', gap: 70}}>
        <div>
          <h2 style={{fontSize: 88, lineHeight: 0.98, margin: 0, fontWeight: 920}}>Built tonight</h2>
          <div style={{marginTop: 34, fontSize: 33, lineHeight: 1.25, color: palette.muted}}>
            The platform now has review-ready briefs for the major open gates, plus a fresh unattended-loop evidence path that does not start any scheduler.
          </div>
          <div style={{marginTop: 52, border: `2px solid ${palette.red}`, padding: 28, background: 'rgba(217,77,61,0.12)'}}>
            <div style={{fontSize: 27, color: palette.red, fontWeight: 900, textTransform: 'uppercase'}}>Safety invariant</div>
            <div style={{fontSize: 36, lineHeight: 1.13, marginTop: 14, fontWeight: 850}}>
              Output can propose, brief, and record evidence. It does not close release gates.
            </div>
          </div>
        </div>
        <BulletList items={completed} start={18} color={palette.green} />
      </div>
      <div style={{position: 'absolute', left: 112, right: 112, bottom: 78, height: 8, background: palette.line}}>
        <div style={{width: `${interpolate(frame, [0, 120], [0, 100], {extrapolateRight: 'clamp'})}%`, height: '100%', background: palette.green}} />
      </div>
    </HudShell>
  );
};

const RemainingSlide: React.FC = () => {
  return (
    <HudShell label="Open production gates">
      <div style={{position: 'absolute', left: 112, top: 150, right: 112}}>
        <h2 style={{fontSize: 84, lineHeight: 1, margin: 0, fontWeight: 920}}>What is left</h2>
        <div style={{fontSize: 34, lineHeight: 1.22, color: palette.muted, marginTop: 24, maxWidth: 1320}}>
          The remaining work is mostly human evidence and approved runtime validation, not unbounded code execution.
        </div>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 44, marginTop: 58}}>
          <BulletList items={left.slice(0, 3)} start={20} color={palette.amber} />
          <BulletList items={left.slice(3)} start={46} color={palette.amber} />
        </div>
      </div>
      <div style={{position: 'absolute', left: 112, right: 112, bottom: 82, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 18}}>
        {['No silent cloud spend', 'No background daemon', 'No publication without sign-off'].map((item, index) => (
          <div key={item} style={{border: `2px solid ${palette.amber}`, padding: 22, fontSize: 28, fontWeight: 850, color: palette.amber}}>
            {String(index + 1).padStart(2, '0')} / {item}
          </div>
        ))}
      </div>
    </HudShell>
  );
};

const DecisionsSlide: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <HudShell label="Human decisions">
      <div style={{position: 'absolute', left: 112, top: 146, width: 820}}>
        <h2 style={{fontSize: 82, lineHeight: 1, margin: 0, fontWeight: 920}}>Decisions still needed</h2>
        <div style={{fontSize: 34, lineHeight: 1.25, color: palette.muted, marginTop: 26}}>
          The next phase should pick one proof path, run it intentionally, and record accepted evidence in the release ledger.
        </div>
      </div>
      <div style={{position: 'absolute', right: 112, top: 132, width: 835}}>
        <BulletList items={decisions} start={16} color={palette.cyan} />
      </div>
      <div
        style={{
          position: 'absolute',
          left: 112,
          right: 112,
          bottom: 82,
          border: `2px solid ${palette.green}`,
          background: 'rgba(85,214,138,0.1)',
          padding: '30px 36px',
          opacity: fade(frame, 88),
        }}
      >
        <div style={{fontSize: 30, color: palette.green, fontWeight: 900, textTransform: 'uppercase'}}>Recommended next move</div>
        <div style={{fontSize: 43, lineHeight: 1.1, fontWeight: 900, marginTop: 10}}>
          Pick the first human-evidence gate to close: mobile device, Gemini Live, signing, external security, or unattended policy acceptance.
        </div>
      </div>
    </HudShell>
  );
};

export const JarvisOvernightBrief: React.FC = () => {
  return (
    <>
      <Sequence from={0} durationInFrames={180}>
        <TitleSlide />
      </Sequence>
      <Sequence from={180} durationInFrames={240}>
        <CompletedSlide />
      </Sequence>
      <Sequence from={420} durationInFrames={240}>
        <RemainingSlide />
      </Sequence>
      <Sequence from={660} durationInFrames={240}>
        <DecisionsSlide />
      </Sequence>
    </>
  );
};
