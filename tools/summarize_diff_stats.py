import re
from datetime import datetime

def parse_diff_stats(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    stats = {}
    for line in lines[1:]:  # Skip the first line with the date
        match = re.match(r'(.+):\s+(\d+\.\d+)', line)
        if match:
            filename = match.group(1)
            value = float(match.group(2))
            stats[filename] = value

    return stats

def summarize_stats(stats):
    if not stats:
        print("No valid statistics found.")
        return

    max_file = max(stats, key=stats.get)
    min_file = min(stats, key=stats.get)
    mean_value = sum(stats.values()) / len(stats)
    above_threshold = [file for file, value in stats.items() if value > 0.03]

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Summary of image differences (generated on {current_time}):")
    print("")
    print(f"- Total files: {len(stats)}")
    print(f"- Maximum difference: {max_file} with value {stats[max_file]}")
    print(f"- Minimum difference: {min_file} with value {stats[min_file]}")
    print(f"- Mean difference: {mean_value}")
    if above_threshold:
        print("- Files above 3% threshold:")
        for file in above_threshold:
            print(f"  - {file}: {stats[file]}")
    else:
        print("- No files above 3% threshold.")

if __name__ == "__main__":
    diff_stats_file = "generated/image_diff_stats.txt"
    stats = parse_diff_stats(diff_stats_file)
    summarize_stats(stats)
