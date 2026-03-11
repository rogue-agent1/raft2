#!/usr/bin/env python3
"""raft2 — Raft consensus protocol simulation. Zero deps."""
import random

FOLLOWER, CANDIDATE, LEADER = 'follower', 'candidate', 'leader'

class LogEntry:
    def __init__(self, term, command):
        self.term, self.command = term, command
    def __repr__(self): return f"({self.term}:{self.command})"

class RaftNode:
    def __init__(self, node_id, peers):
        self.id = node_id
        self.peers = peers
        self.state = FOLLOWER
        self.term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = -1
        self.timeout = random.randint(5, 15)
        self.timer = 0
        self.votes = 0

    def tick(self, cluster):
        self.timer += 1
        if self.state == LEADER:
            self._send_heartbeats(cluster)
            self.timer = 0
        elif self.timer >= self.timeout:
            self._start_election(cluster)

    def _start_election(self, cluster):
        self.state = CANDIDATE
        self.term += 1
        self.voted_for = self.id
        self.votes = 1
        self.timer = 0
        self.timeout = random.randint(5, 15)
        for pid in self.peers:
            if cluster[pid]._handle_vote_request(self.id, self.term):
                self.votes += 1
        if self.votes > (len(self.peers) + 1) // 2:
            self.state = LEADER

    def _handle_vote_request(self, candidate_id, term):
        if term > self.term:
            self.term = term
            self.state = FOLLOWER
            self.voted_for = candidate_id
            self.timer = 0
            return True
        return False

    def _send_heartbeats(self, cluster):
        for pid in self.peers:
            cluster[pid]._handle_heartbeat(self.term)

    def _handle_heartbeat(self, term):
        if term >= self.term:
            self.term = term
            self.state = FOLLOWER
            self.timer = 0

    def propose(self, command, cluster):
        if self.state != LEADER: return False
        entry = LogEntry(self.term, command)
        self.log.append(entry)
        acks = 1
        for pid in self.peers:
            cluster[pid].log.append(entry)
            acks += 1
        if acks > (len(self.peers) + 1) // 2:
            self.commit_index = len(self.log) - 1
        return True

def main():
    random.seed(42)
    ids = ['A', 'B', 'C', 'D', 'E']
    cluster = {}
    for nid in ids:
        cluster[nid] = RaftNode(nid, [p for p in ids if p != nid])

    print("Raft Consensus Simulation (5 nodes):\n")
    for tick in range(30):
        for nid in ids:
            cluster[nid].tick(cluster)
        leaders = [nid for nid in ids if cluster[nid].state == LEADER]
        if leaders:
            print(f"  Tick {tick:>2}: Leader={leaders[0]}, term={cluster[leaders[0]].term}")
            if tick == 15:
                cluster[leaders[0]].propose("SET x=1", cluster)
                print(f"          Proposed 'SET x=1'")
            break  # stable after first election
    # Show final state
    leader = next(nid for nid in ids if cluster[nid].state == LEADER)
    for tick in range(30):
        for nid in ids:
            cluster[nid].tick(cluster)
    cluster[leader].propose("SET x=1", cluster)
    cluster[leader].propose("SET y=2", cluster)
    print(f"\nFinal state:")
    for nid in ids:
        n = cluster[nid]
        print(f"  {nid}: {n.state:>10}, term={n.term}, log={n.log}, commit={n.commit_index}")

if __name__ == "__main__":
    main()
