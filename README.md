# PagerDuty Notification Manager

Interactive terminal tool for viewing and managing PagerDuty on-call notification rules across your organization.

## Features

- Browse users (all or by team)
- View notification rules and contact methods per user
- Edit, add, or delete notification rules individually
- Bulk update selected users — pick from all users or a team, multi-select with checkboxes, then apply rules to just those users
- Bulk apply rules by team, escalation policy, or org-wide
- Compliance reporting showing who matches, who's partial, who's missing

## Installation

```bash
pip install -e .
```

## Usage

```bash
pd-notify
```

You'll be prompted for your PagerDuty API token (input is masked). Alternatively, set it as an environment variable:

```bash
export PAGERDUTY_API_TOKEN=your-token-here
pd-notify
```

## Requirements

- Python 3.9+
- PagerDuty API token with admin permissions (to manage notification rules for other users)

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
