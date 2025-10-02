#!/usr/bin/env python3
import re
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import csv

# Regex patterns
LINE_PATTERN = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?:\s?[APMapm]{2})?) - (.*?): (.*)$")
ADDED_PATTERN = re.compile(r"^(.*) added (.*)$")  # system message: X added Y
JOINED_PATTERN = re.compile(r"^(.*) joined using this group's invite link$")  # joined via link

# Parse date function
def parse_date(date_str):
    formats = [
        "%d/%m/%Y, %H:%M",
        "%d/%m/%y, %H:%M",
        "%m/%d/%Y, %I:%M %p",
        "%m/%d/%y, %I:%M %p"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

# Analyze WhatsApp chat
def analyze_chat(file_path):
    participants = defaultdict(lambda: {"messages": 0, "last": None})
    total_messages = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Handle "added" messages
            m_added = ADDED_PATTERN.match(line)
            if m_added:
                added_member = m_added.group(2).strip()
                participants[added_member]  # initialize with 0 messages
                continue

            # Handle "joined using link" messages
            m_joined = JOINED_PATTERN.match(line)
            if m_joined:
                joined_member = m_joined.group(1).strip()
                participants[joined_member]  # initialize with 0 messages
                continue

            # Normal messages
            m = LINE_PATTERN.match(line)
            if not m:
                continue
            date_str, sender, msg = m.groups()
            dt = parse_date(date_str)
            if dt is None:
                continue

            participants[sender]["messages"] += 1
            total_messages += 1
            if (participants[sender]["last"] is None) or (dt > participants[sender]["last"]):
                participants[sender]["last"] = dt

    # Calculate contribution %
    for sender, stats in participants.items():
        stats["contribution"] = round(stats["messages"]/total_messages*100, 2) if total_messages else 0

    return participants, total_messages

# Determine active/inactive counts
def member_status_counts(participants, inactivity_days=90):
    now = datetime.now()
    active_count = 0
    inactive_count = 0
    for stats in participants.values():
        if stats["messages"] >= 1 and stats["contribution"] >= 1 and stats["last"] and (now - stats["last"]).days <= inactivity_days:
            active_count += 1
        else:
            inactive_count += 1
    return active_count, inactive_count

# Print console report
def print_report(participants, total_messages):
    active_count, inactive_count = member_status_counts(participants)
    total_members = len(participants)
    print(f"\nTotal Members: {total_members} | Active: {active_count} | Inactive: {inactive_count}")
    print(f"Total Messages in Group: {total_messages}\n")
    print(f"{'Participant':30} {'Messages':10} {'Contribution (%)':15} {'Status':10}")
    print("-"*75)

    now = datetime.now()
    sorted_participants = sorted(
        participants.items(),
        key=lambda x: (
            0 if x[1]["messages"] >= 1 and x[1]["contribution"] >= 1 and x[1]["last"] and (now - x[1]["last"]).days <= 90 else 1,
            -x[1]["messages"]
        )
    )

    for sender, stats in sorted_participants:
        status = "Inactive"
        if stats["messages"] >= 1 and stats["contribution"] >= 1 and stats["last"] and (now - stats["last"]).days <= 90:
            status = "Active"
        print(f"{sender:30} {stats['messages']:10} {stats['contribution']:15} {status:10}")

# Export CSV report
def export_csv(participants, filename="activity_report.csv"):
    now = datetime.now()
    active_count, inactive_count = member_status_counts(participants)
    total_members = len(participants)
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Participant", "Messages", "Contribution (%)", "Status"])
        for sender, stats in participants.items():
            status = "Inactive"
            if stats["messages"] >= 1 and stats["contribution"] >= 1 and stats["last"] and (now - stats["last"]).days <= 90:
                status = "Active"
            writer.writerow([sender, stats["messages"], stats["contribution"], status])
        # Summary stats
        writer.writerow([])
        writer.writerow(["Total Members", total_members])
        writer.writerow(["Active Members", active_count])
        writer.writerow(["Inactive Members", inactive_count])
    print(f"\nCSV report exported as {filename}")

# Top contributors chart
def plot_leaderboard(participants):
    sorted_participants = sorted(participants.items(), key=lambda x: x[1]['messages'], reverse=True)[:5]
    names = [x[0] for x in sorted_participants]
    msgs = [x[1]['messages'] for x in sorted_participants]

    plt.figure(figsize=(8,5))
    bars = plt.bar(names, msgs, color="#4CAF50")
    plt.title("Top 5 Contributors")
    plt.xlabel("Participants")
    plt.ylabel("Messages Sent")

    if bars:
        bars[0].set_color("#FFD700")  # highlight top contributor

    for bar, count in zip(bars, msgs):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height()+1, str(count), ha='center', fontsize=10)

    plt.show()

# Active vs inactive pie chart
def plot_activity_pie(participants, inactivity_days=90):
    inactive_count = 0
    now = datetime.now()
    for stats in participants.values():
        if stats["messages"] < 1 or stats["contribution"] < 1 or stats["last"] is None or (now - stats["last"]).days > inactivity_days:
            inactive_count += 1
    active_count = len(participants) - inactive_count

    plt.figure(figsize=(6,6))
    plt.pie([active_count, inactive_count], labels=["Active", "Inactive"], autopct="%1.1f%%", colors=["#4CAF50", "#F44336"])
    plt.title("Active vs Inactive Members")
    plt.show()

# Main function
def main():
    chat_file = "chat.txt"  # replace with your exported WhatsApp chat file
    participants, total_messages = analyze_chat(chat_file)
    print_report(participants, total_messages)
    export_csv(participants)
    plot_leaderboard(participants)
    plot_activity_pie(participants)

if __name__ == "__main__":
    main()
