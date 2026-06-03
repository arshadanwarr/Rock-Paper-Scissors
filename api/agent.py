"""
Q-Learning Agent for Rock Paper Scissors
=========================================
State  : (ai_last_move, human_last_move)  — integers 0-2, or 9 for "start"
Actions: 0=Rock, 1=Paper, 2=Scissors
Reward : +1 win  |  0 draw  |  -1 loss
"""

import random
import json
import os
from typing import Optional

MOVES       = ["Rock", "Paper", "Scissors"]
WINS        = {(0,2), (1,0), (2,1)}   # (winner, loser) pairs
START_STATE = (9, 9)


class QLearningAgent:
    def __init__(
        self,
        alpha: float  = 0.30,   # learning rate
        gamma: float  = 0.90,   # discount factor
        epsilon: float = 1.00,  # exploration rate
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.995,
    ):
        self.alpha         = alpha
        self.gamma         = gamma
        self.epsilon       = epsilon
        self.epsilon_min   = epsilon_min
        self.epsilon_decay = epsilon_decay

        # Q-table: dict of {state_key -> [Q_rock, Q_paper, Q_scissors]}
        self.q_table: dict[str, list[float]] = {}

        # History for graphs / stats
        self.episode_rewards: list[float] = []
        self.cumulative_rewards: list[float] = []
        self.total_reward: float = 0.0
        self.episodes: int = 0
        self.wins: int = 0
        self.losses: int = 0
        self.draws: int = 0

        # Tracking
        self.ai_last_move:  int = 9
        self.hum_last_move: int = 9

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _key(ai_last: int, hum_last: int) -> str:
        return f"{ai_last},{hum_last}"

    def _get_q(self, key: str) -> list[float]:
        if key not in self.q_table:
            self.q_table[key] = [0.0, 0.0, 0.0]
        return self.q_table[key]

    # ------------------------------------------------------------------ core
    def choose_action(self, state_key: str, force_exploit: bool = False) -> int:
        """ε-greedy action selection."""
        if not force_exploit and random.random() < self.epsilon:
            return random.randint(0, 2)
        q = self._get_q(state_key)
        max_q = max(q)
        best = [i for i, v in enumerate(q) if v == max_q]
        return random.choice(best)

    def update(
        self,
        state_key: str,
        action: int,
        reward: float,
        next_state_key: str,
    ) -> None:
        """Bellman update:  Q(s,a) ← Q(s,a) + α[r + γ·maxQ(s',·) − Q(s,a)]"""
        q      = self._get_q(state_key)
        q_next = self._get_q(next_state_key)
        q[action] += self.alpha * (reward + self.gamma * max(q_next) - q[action])

    def decay_epsilon(self) -> None:
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    # ------------------------------------------------------------------ outcome
    @staticmethod
    def compute_reward(ai_move: int, hum_move: int) -> tuple[float, str]:
        if (ai_move, hum_move) in WINS:
            return +1.0, "ai"
        if (hum_move, ai_move) in WINS:
            return -1.0, "human"
        return 0.0, "draw"

    # ------------------------------------------------------------------ play
    def play_round(self, hum_move: int, exploit: bool = True) -> dict:
        """
        Called when a human makes a move.
        Returns a dict with all round info for the API.
        """
        state_key = self._key(self.ai_last_move, self.hum_last_move)
        ai_move   = self.choose_action(state_key, force_exploit=exploit)
        reward, outcome = self.compute_reward(ai_move, hum_move)

        next_state_key = self._key(ai_move, hum_move)
        self.update(state_key, ai_move, reward, next_state_key)
        self.decay_epsilon()

        # bookkeeping
        self.ai_last_move  = ai_move
        self.hum_last_move = hum_move
        self.episodes      += 1
        self.total_reward  += reward
        self.episode_rewards.append(reward)
        self.cumulative_rewards.append(
            round(self.total_reward / self.episodes, 4)
        )
        if outcome == "ai":
            self.wins += 1
        elif outcome == "human":
            self.losses += 1
        else:
            self.draws += 1

        return {
            "ai_move":    ai_move,
            "hum_move":   hum_move,
            "outcome":    outcome,
            "reward":     reward,
            "episode":    self.episodes,
            "epsilon":    round(self.epsilon, 4),
        }

    def auto_train(self, n: int) -> dict:
        """Train agent against random opponent for n episodes."""
        for _ in range(n):
            hum_move = random.randint(0, 2)
            self.play_round(hum_move, exploit=False)
        return self.get_stats()

    # ------------------------------------------------------------------ state
    def reset(self) -> None:
        self.__init__(
            self.alpha, self.gamma,
            1.0, self.epsilon_min, self.epsilon_decay
        )

    def get_stats(self) -> dict:
        total = self.wins + self.losses + self.draws
        return {
            "episodes":   self.episodes,
            "wins":       self.wins,
            "losses":     self.losses,
            "draws":      self.draws,
            "total":      total,
            "win_rate":   round(self.wins / total * 100, 1) if total else 0,
            "avg_reward": round(self.total_reward / self.episodes, 4) if self.episodes else 0,
            "total_reward": round(self.total_reward, 4),
            "epsilon":    round(self.epsilon, 4),
            "alpha":      self.alpha,
            "gamma":      self.gamma,
        }

    def get_q_table(self) -> dict:
        """Return full Q-table with human-readable state labels."""
        states = [
            ("Rock,Rock",     "0,0"), ("Rock,Paper",    "0,1"),
            ("Rock,Scissors", "0,2"), ("Paper,Rock",    "1,0"),
            ("Paper,Paper",   "1,1"), ("Paper,Scissors","1,2"),
            ("Scissors,Rock", "2,0"), ("Scissors,Paper","2,1"),
            ("Scissors,Scissors","2,2"), ("Start",      "9,9"),
        ]
        result = []
        for label, key in states:
            q = self._get_q(key)
            result.append({
                "state": label,
                "key":   key,
                "rock":  round(q[0], 4),
                "paper": round(q[1], 4),
                "scissors": round(q[2], 4),
                "best_action": MOVES[q.index(max(q))],
            })
        return result

    def get_reward_history(self) -> dict:
        """Return episode rewards and running average for charting."""
        return {
            "episode_rewards":    self.episode_rewards[-500:],
            "cumulative_rewards": self.cumulative_rewards[-500:],
            "episodes":           list(range(
                max(1, self.episodes - 499), self.episodes + 1
            )),
        }

    # ------------------------------------------------------------------ persist
    def save(self, path: str = "agent_state.json") -> None:
        data = {
            "q_table":           self.q_table,
            "epsilon":           self.epsilon,
            "alpha":             self.alpha,
            "gamma":             self.gamma,
            "epsilon_min":       self.epsilon_min,
            "epsilon_decay":     self.epsilon_decay,
            "episodes":          self.episodes,
            "wins":              self.wins,
            "losses":            self.losses,
            "draws":             self.draws,
            "total_reward":      self.total_reward,
            "episode_rewards":   self.episode_rewards,
            "cumulative_rewards":self.cumulative_rewards,
            "ai_last_move":      self.ai_last_move,
            "hum_last_move":     self.hum_last_move,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str = "agent_state.json") -> bool:
        if not os.path.exists(path):
            return False
        with open(path) as f:
            data = json.load(f)
        self.q_table           = data.get("q_table", {})
        self.epsilon           = data.get("epsilon", 1.0)
        self.alpha             = data.get("alpha", 0.30)
        self.gamma             = data.get("gamma", 0.90)
        self.epsilon_min       = data.get("epsilon_min", 0.05)
        self.epsilon_decay     = data.get("epsilon_decay", 0.995)
        self.episodes          = data.get("episodes", 0)
        self.wins              = data.get("wins", 0)
        self.losses            = data.get("losses", 0)
        self.draws             = data.get("draws", 0)
        self.total_reward      = data.get("total_reward", 0.0)
        self.episode_rewards   = data.get("episode_rewards", [])
        self.cumulative_rewards= data.get("cumulative_rewards", [])
        self.ai_last_move      = data.get("ai_last_move", 9)
        self.hum_last_move     = data.get("hum_last_move", 9)
        return True
