from MessagesWrapped import MessagesWrapped
from Grapher import *


# Minimal helper to safely attempt plotting
def safe_plot(plot_fn, name, data, **kwargs):
    if not data:
        print(f"{name}: no data (None or empty). Skipping plot.")
        return
    try:
        plot_fn(data, **kwargs)
    except Exception as e:
        print(f"{name}: plotting failed: {e}")


def print_conversation_comparison(comparisons):
    if not comparisons:
        print("No conversations loaded or comparison empty.")
        return
    print(f"\nTOP {len(comparisons)} CONVERSATIONS (summary):")
    for i, meta in enumerate(comparisons, 1):
        print(f"{i}. {meta.get('name')}")
        print(f"   Participants: {', '.join(meta.get('participant_names', [])[:3])}{'...' if len(meta.get('participant_names', [])) > 3 else ''}")
        print(f"   Type: {'Group Chat' if meta.get('is_group_chat') else '1-on-1'} ({meta.get('participant_count', 0)} people)")
        print(f"   Messages: {meta.get('total_messages', 0):,} ({meta.get('messages_per_day', 0):.1f}/day)")
        print()


from MessagesWrapped import MessagesWrapped
from Grapher import *


# Minimal helper to safely attempt plotting
def safe_plot(plot_fn, name, data, **kwargs):
    if not data:
        print(f"{name}: no data (None or empty). Skipping plot.")
        return
    try:
        plot_fn(data, **kwargs)
    except Exception as e:
        print(f"{name}: plotting failed: {e}")


def print_conversation_comparison(comparisons):
    if not comparisons:
        print("No conversations loaded or comparison empty.")
        return
    print(f"\nTOP {len(comparisons)} CONVERSATIONS (summary):")
    for i, meta in enumerate(comparisons, 1):
        print(f"{i}. {meta.get('name')}")
        print(f"   Participants: {', '.join(meta.get('participant_names', [])[:3])}{'...' if len(meta.get('participant_names', [])) > 3 else ''}")
        print(f"   Type: {'Group Chat' if meta.get('is_group_chat') else '1-on-1'} ({meta.get('participant_count', 0)} people)")
        print(f"   Messages: {meta.get('total_messages', 0):,} ({meta.get('messages_per_day', 0):.1f}/day)")
        print()


if __name__ == '__main__':
    wrapped = MessagesWrapped(conversations_dir='exports', max_workers=8, show_progress=True, use_processes=False)
    summary = wrapped.get_2025_messages_wrapped()

    print('\n=== 2025 SUMMARY ===')
    print(f"Total messages (You): {summary.get('total_number_messages')}")
    print(f"Total words (You): {summary.get('total_words_sent')}")
    print(f"Non-group contacts messaged (>=1): {summary.get('non_gc_with_min2_msgs')}")

    # Conversation comparison
    print_conversation_comparison(summary.get('conversation_comparison'))

    # Top chats by messages and attachments
    print('\nTop chats by messages:')
    for i, (label, cnt) in enumerate(summary.get('top_n_chats_by_messages', []), 1):
        print(f"  {i}. {label}: {cnt}")

    print('\nTop chats by attachments:')
    for i, (label, cnt) in enumerate(summary.get('top_n_chats_by_attachments', []), 1):
        print(f"  {i}. {label}: {cnt}")

    # Response time extremes
    rt = summary.get('top_bottom_n_non_gc_by_response_time', {}) or {}
    print('\nTop (slowest) non-group chats by median response time:')
    for label, val in rt.get('top', []):
        print(f"  {label}: {val:.1f} minutes")
    print('\nBottom (fastest) non-group chats by median response time:')
    for label, val in rt.get('bottom', []):
        print(f"  {label}: {val:.1f} minutes")

    # Graph everything graphable
    print('\n=== Generating plots (if data present) ===')

    safe_plot(plot_top_emojis, 'Top Emojis', summary.get('top_emojis_data'))
    safe_plot(plot_emoji_timeline, 'Emoji Timeline', summary.get('emoji_timeline'))
    safe_plot(plot_top_chats_timeline, 'Top Chats Timeline', summary.get('top_chats_timeline'))
    safe_plot(plot_messages_timeline, 'Messages Timeline', summary.get('messages_sent_timeline'))
    safe_plot(plot_messages_by_hour, 'Messages By Hour', summary.get('messages_sent_by_hour'))
    safe_plot(plot_avg_response_time_by_hour, 'Response Time By Hour', summary.get('response_time_by_hour'), metric_name='Median')
    safe_plot(plot_words_per_message_by_hour, 'Words Per Message By Hour', summary.get('words_per_message_per_hour'), metric_name='Median')
    safe_plot(plot_total_words_timeline, 'Total Words Timeline', summary.get('messages_sent_timeline'))

    print('\nDone.')
