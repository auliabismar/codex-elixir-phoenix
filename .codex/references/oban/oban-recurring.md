# Oban Recurring Jobs

## Overview
Oban supports cron-style scheduled jobs using the `cron` option.

## Cron Configuration
```elixir
config :my_app, Oban,
  repo: MyApp.Repo,
  plugins: [
    {Oban.Plugins.Cron,
     crontab: [
       {"* * * * *", MyApp.Workers.MinuteJob},
       {"0 9 * * 1-5", MyApp.Workers.WeekdayMorning},
       {"@daily", MyApp.Workers.DailyCleanup}
     ]}
  ]
```

## Cron Format
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6)
│ │ │ │ │
* * * * *
```

## Special Syntax
- `@yearly` / `@annually` - Once a year
- `@monthly` - Once a month
- `@weekly` - Once a week
- `@daily` / `@midnight` - Once a day
- `@hourly` - Once an hour