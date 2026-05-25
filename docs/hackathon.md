# Hackathon context

Official event: **[Pirates of the Coral-bean](https://www.wemakedevs.org/hackathons/coral)** (WeMakeDevs + Coral)

| | |
|---|---|
| **Dates** | May 25 – May 31 |
| **Format** | Online |
| **Prize pool** | $10,000+ (see hackathon page for track prizes) |
| **Our track** | **Track 1 — Build an Enterprise Agent** |

## What is Coral?

From the [hackathon overview](https://www.wemakedevs.org/hackathons/coral):

- Any API, database, or file becomes a **SQL table**
- **Cross-source JOINs** in one query (e.g. GitHub + Slack + Sentry)
- **100% local** — credentials and data stay on your machine
- **CLI or MCP** — auth, pagination, rate limits handled by Coral
- No ETL, no warehouse, no per-source glue in the agent

## Relevant example voyages (Track 1)

| Example | Sources | Relation to our project |
|---------|---------|-------------------------|
| Coding Agent Debugger | GitHub + Sentry + Slack + Datadog | Same multi-source debug story |
| **AI SRE Investigator** | PagerDuty + Datadog + GitHub + StatusGator | **Closest match** — incident + deploy + metrics correlation |
| Customer Escalation Agent | Intercom + Sentry + Grafana + Slack | Support + errors + internal context |

We are building **Production Incident Intelligence Agent**: automated investigation + report, with severity-based remediation (autonomous vs human-paired).

## Judging criteria (official)

1. **Potential impact** — meaningful problem + Coral retrieval
2. **Creativity & originality** — unique use of cross-source SQL
3. **Learning & growth** — especially first-time Coral users
4. **Technical implementation** — quality of Coral integration and queries
5. **Aesthetics & UX** — dashboard, CLI, or agent interface
6. **Best use of Coral** — SQL interface, joins, caching

## Special bounties (optional)

- Early bird / social share swag
- Discord `#show-and-tell` + social post showcase
- **Chart new waters** — custom Coral source specs ($100 + charity donation for top specs)
- **Captain's log** — end-to-end “how to build X” blog guides

## Coral quickstart

```bash
brew install withcoral/tap/coral
coral source add <source>
```

Docs, Discord, and GitHub links are on the [hackathon sponsor section](https://www.wemakedevs.org/hackathons/coral).

## Registration

Register and form a team (up to 4) via the hackathon site: [Register](https://www.wemakedevs.org/hackathons/coral).
