import React from 'react';
import {Composition} from 'remotion';
import {JarvisCodexPlan} from './scenes/JarvisCodexPlan';

export const Root: React.FC = () => {
  return (
    <Composition
      id="JarvisCodexPlan"
      component={JarvisCodexPlan}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: 'Jarvis Codex',
        subtitle: 'Local-first voice, memory, approvals, and Codex handoff loop',
      }}
    />
  );
};
