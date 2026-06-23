import React from 'react';
import {Composition} from 'remotion';
import {JarvisCodexPlan} from './scenes/JarvisCodexPlan';
import {JarvisOvernightBrief} from './scenes/JarvisOvernightBrief';

export const Root: React.FC = () => {
  return (
    <>
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
      <Composition
        id="JarvisOvernightBrief"
        component={JarvisOvernightBrief}
        durationInFrames={900}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
