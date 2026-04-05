# Hevy API Webhooks & Events

## Current Status

The Hevy API (v1) **does not support webhooks** for push-based event notifications. There are no endpoints for subscribing to events such as "workout completed", "routine created", etc.

## Available: Polling-Based Events

The API does provide a **polling-based event system** for tracking changes to workouts:

### Workout Events Endpoint

```
GET /v1/workouts/events?since=<ISO8601>&page=1&pageSize=10
```

This endpoint returns workout update and delete events since a given timestamp. It can be used to detect:

- Workouts that were **updated** after a certain time
- Workouts that were **deleted** after a certain time

#### CLI Usage

```bash
# List recent workout events
hevy workouts events

# Events since a specific date
hevy workouts events --since 2024-01-01T00:00:00Z
```

#### Polling Strategy

To simulate real-time notifications, you can poll this endpoint periodically:

1. Store the last poll timestamp
2. Call `/v1/workouts/events?since=<last_poll_time>`
3. Process any returned events
4. Update the stored timestamp

**Recommended polling interval:** 5-15 minutes (to stay within rate limits).

## Rate Limits

The Hevy API enforces rate limits (HTTP 429). The CLI handles this automatically with exponential backoff retries, but polling scripts should respect a reasonable interval.

## Future Considerations

If Hevy adds webhook support in the future, this CLI could be extended with:

- `hevy webhooks list` — List webhook subscriptions
- `hevy webhooks create --url <callback_url> --event workout.completed` — Subscribe to events
- `hevy webhooks delete <webhook_id>` — Remove a subscription

Until then, the recommended approach is polling via the workout events endpoint.

## Alternatives for Real-Time Notifications

For users who need real-time notifications, consider:

1. **Cron job + events endpoint**: Set up a cron job that polls `/v1/workouts/events` and sends notifications (email, Slack, etc.) when new events are detected.
2. **CI/CD integration**: Use `hevy workouts events --since` in a scheduled pipeline to trigger downstream actions.
