from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Literal

from .policy import PolicyDecision, PolicyProfile, classify_command


IntentType = Literal["command_proposal", "agent_handoff", "note", "unknown"]
IntentTarget = Literal["codex", "antigravity", "operator", "none"]


COMMAND_PREFIX = re.compile(
    r"^\s*(?:run|execute|shell|terminal)\s+(?:the\s+)?(?:command\s+)?(?P<command>.+?)\s*$",
    re.IGNORECASE,
)
AGENT_PREFIX = re.compile(
    r"^\s*(?:ask|have|send|route)\s+(?P<target>codex|antigravity|ag)\s+(?:to\s+)?(?P<objective>.+?)\s*$",
    re.IGNORECASE,
)
NOTE_PREFIX = re.compile(r"^\s*(?:note|remember|capture)\s+(?P<note>.+?)\s*$", re.IGNORECASE)
FILE_CONTEXT_PREFIX = re.compile(
    r"^\s*(?:grab|open|read|load|pull(?:\s+up)?)\s+(?:this\s+|the\s+)?(?:file|path)\s+"
    r"(?:in|at|from|under|located\s+at)?\s*(?:this\s+)?(?:location\s+)?(?P<path>.+?)\s*$",
    re.IGNORECASE,
)
CODEBASE_EXPLORE_PREFIX = re.compile(
    r"^\s*(?:explore|inspect|map|review)\s+(?:this\s+|the\s+)?(?:codebase|repo|repository|project)"
    r"(?:\s+(?P<objective>.+?))?\s*$",
    re.IGNORECASE,
)
FEATURE_PLAN_PREFIX = re.compile(
    r"^\s*(?:plan|scope|design)\s+(?:this\s+|the\s+)?(?:feature|change|implementation|work)"
    r"(?:\s+(?P<objective>.+?))?\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class VoiceIntentProposal:
    proposal_id: str
    transcript: str
    intent_type: IntentType
    target: IntentTarget
    summary: str
    command: str | None = None
    policy: PolicyDecision | None = None

    @property
    def execution_authority(self) -> bool:
        return False

    @property
    def approval_required(self) -> bool:
        return self.intent_type in {"command_proposal", "agent_handoff"}

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "proposal_id": self.proposal_id,
            "transcript": self.transcript,
            "intent_type": self.intent_type,
            "target": self.target,
            "summary": self.summary,
            "approval_required": self.approval_required,
            "execution_authority": False,
            "routed_as_command": False,
        }
        if self.command is not None:
            data["command"] = self.command
        if self.policy is not None:
            data["policy"] = self.policy.to_dict()
        return data


def propose_voice_intent(transcript: str, *, profile: PolicyProfile = "observe") -> VoiceIntentProposal:
    text = " ".join(transcript.strip().split())
    if not text:
        raise ValueError("voice transcript is required")

    command_match = COMMAND_PREFIX.match(text)
    if command_match:
        command = command_match.group("command").strip()
        policy = classify_command(command, profile)
        return VoiceIntentProposal(
            proposal_id=_new_proposal_id(),
            transcript=text,
            intent_type="command_proposal",
            target="operator",
            summary="Voice-origin command proposal requires explicit confirmation before execution.",
            command=command,
            policy=policy,
        )

    agent_match = AGENT_PREFIX.match(text)
    if agent_match:
        target = agent_match.group("target").lower()
        normalized_target: IntentTarget = "antigravity" if target in {"ag", "antigravity"} else "codex"
        objective = agent_match.group("objective").strip()
        return VoiceIntentProposal(
            proposal_id=_new_proposal_id(),
            transcript=text,
            intent_type="agent_handoff",
            target=normalized_target,
            summary=f"Voice-origin {normalized_target} handoff proposal requires explicit confirmation: {objective}",
            command=None,
            policy=None,
        )

    file_context_match = FILE_CONTEXT_PREFIX.match(text)
    if file_context_match:
        path = file_context_match.group("path").strip()
        return _codex_handoff(text, f"read the requested file or path for context: {path}")

    codebase_explore_match = CODEBASE_EXPLORE_PREFIX.match(text)
    if codebase_explore_match:
        objective = (codebase_explore_match.group("objective") or "and summarize the relevant structure").strip()
        return _codex_handoff(text, f"explore the codebase {objective}")

    feature_plan_match = FEATURE_PLAN_PREFIX.match(text)
    if feature_plan_match:
        objective = (feature_plan_match.group("objective") or "and produce an implementation plan").strip()
        return _codex_handoff(text, f"plan the feature {objective}")

    note_match = NOTE_PREFIX.match(text)
    if note_match:
        return VoiceIntentProposal(
            proposal_id=_new_proposal_id(),
            transcript=text,
            intent_type="note",
            target="operator",
            summary="Voice-origin note captured as planning context only.",
        )

    return VoiceIntentProposal(
        proposal_id=_new_proposal_id(),
        transcript=text,
        intent_type="unknown",
        target="none",
        summary="Voice transcript was not routed; operator review is required.",
    )


def _codex_handoff(transcript: str, objective: str) -> VoiceIntentProposal:
    return VoiceIntentProposal(
        proposal_id=_new_proposal_id(),
        transcript=transcript,
        intent_type="agent_handoff",
        target="codex",
        summary=f"Voice-origin codex handoff proposal requires explicit confirmation: {objective}",
        command=None,
        policy=None,
    )


def _new_proposal_id() -> str:
    return f"voice_intent_{uuid.uuid4().hex[:16]}"
