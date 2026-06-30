from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Exchange:
    user_input: str
    response: str
    timestamp: str
    emotion_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass
class Episode:
    episode_id: str
    user_id: str
    started_at: str
    last_exchange_at: str
    exchanges: list[Exchange] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    distilled_summary: str = ""
    exchange_count: int = 0


@dataclass
class EpisodicMemoryConfig:
    max_exchanges_per_episode: int = 10
    episode_ttl_hours: int = 24
    max_episodes: int = 50


class EpisodicMemoryStore:
    def __init__(self, config: EpisodicMemoryConfig | None = None) -> None:
        self.config = config or EpisodicMemoryConfig()
        self._episodes: dict[str, list[Episode]] = {}

    def record_exchange(
        self,
        user_id: str,
        user_input: str,
        response: str,
        emotion_state: dict[str, Any] | None = None,
    ) -> Episode:
        episodes = self._episodes.setdefault(user_id, [])
        now = datetime.now(timezone.utc).isoformat()
        active = self._get_active_episode(user_id, now)

        if active is None:
            active = Episode(
                episode_id=self._make_id(user_id, now),
                user_id=user_id,
                started_at=now,
                last_exchange_at=now,
            )
            episodes.append(active)

        active.exchanges.append(Exchange(
            user_input=user_input,
            response=response,
            timestamp=now,
            emotion_snapshot=emotion_state or {},
        ))
        active.exchange_count += 1
        active.last_exchange_at = now
        active.facts.extend(self._extract_facts(user_input, response))

        if active.exchange_count >= self.config.max_exchanges_per_episode:
            self._distill(active)

        self._trim(user_id)
        return active

    def get_episodes(self, user_id: str) -> list[Episode]:
        return list(self._episodes.get(user_id, []))

    def get_context_summary(self, user_id: str) -> str:
        episodes = self._episodes.get(user_id, [])
        if not episodes:
            return "No episodic memory yet."
        parts = []
        for ep in episodes[-3:]:
            if ep.distilled_summary:
                parts.append(ep.distilled_summary)
            elif ep.facts:
                parts.append("; ".join(ep.facts[:5]))
        return " | ".join(parts) if parts else "No episodic memory yet."

    def get_facts(self, user_id: str) -> list[str]:
        facts = []
        for ep in self._episodes.get(user_id, []):
            facts.extend(ep.facts)
        return facts

    def _get_active_episode(self, user_id: str, now_iso: str) -> Episode | None:
        episodes = self._episodes.get(user_id, [])
        if not episodes:
            return None
        last = episodes[-1]
        now = datetime.fromisoformat(now_iso)
        started = datetime.fromisoformat(last.started_at)
        hours = (now - started).total_seconds() / 3600
        if hours > self.config.episode_ttl_hours:
            return None
        if last.distilled_summary:
            return None
        return last

    def _distill(self, episode: Episode) -> None:
        fact_counts: dict[str, int] = {}
        for fact in episode.facts:
            normalized = fact.strip().lower()
            fact_counts[normalized] = fact_counts.get(normalized, 0) + 1

        kept = []
        seen = set()
        for fact in episode.facts:
            normalized = fact.strip().lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            if fact_counts[normalized] > 1 or len(episode.facts) <= 3:
                kept.append(fact)

        if not kept:
            kept = episode.facts[-3:] if len(episode.facts) > 3 else episode.facts

        episode.facts = kept
        episode.distilled_summary = " | ".join(kept[:6])
        episode.exchanges = []

    def _extract_facts(self, user_input: str, response: str) -> list[str]:
        facts = []
        input_lower = user_input.lower()
        personal_markers = [
            "my name is", "i am", "i'm", "i work", "i live", "i like",
            "i love", "i hate", "i feel", "i have", "i need", "i want",
            "my favorite", "my job", "my family", "my friend",
        ]
        for marker in personal_markers:
            if marker in input_lower:
                start = input_lower.index(marker)
                sentence_end = user_input.find(".", start)
                if sentence_end == -1:
                    sentence_end = len(user_input)
                fact = user_input[start:sentence_end].strip()
                if fact:
                    facts.append(fact)
                break

        response_lower = response.lower()
        if any(phrase in response_lower for phrase in ["you mentioned", "you said", "you shared"]):
            facts.append(f"Conversation topic: {user_input[:80]}")

        return facts

    def _make_id(self, user_id: str, timestamp: str) -> str:
        raw = f"{user_id}:{timestamp}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def _trim(self, user_id: str) -> None:
        episodes = self._episodes.get(user_id, [])
        if len(episodes) <= self.config.max_episodes:
            return
        self._episodes[user_id] = episodes[-self.config.max_episodes:]
