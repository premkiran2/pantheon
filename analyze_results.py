import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import shutil
import glob

CC_ALGOS = ["cubic", "vivace", "vegas"]

NET_PROFILES = {
    "1": {
        "latency": 5,
        "dl_trace": "mahimahi/traces/TMobile-LTE-driving.down",
        "ul_trace": "mahimahi/traces/TMobile-LTE-driving.up"
    },
    "2": {
        "latency": 200,
        "dl_trace": "mahimahi/traces/TMobile-LTE-short.down",
        "ul_trace": "mahimahi/traces/TMobile-LTE-short.up"
    }
}

def execute_tests():
    for prof_id, prof_config in NET_PROFILES.items():
        print(f"\n--- Running tests for Network Profile {prof_id} (latency = {prof_config['latency']} ms) ---")
        for algo in CC_ALGOS:
            print(f"[INFO] Testing congestion control algorithm: {algo.upper()}")
            result_path = f"results/profile_{prof_id}/{algo}"
            os.makedirs(result_path, exist_ok=True)

            test_command = (
                f"mm-delay {prof_config['latency']} "
                f"mm-link {prof_config['dl_trace']} {prof_config['ul_trace']} -- "
                f"bash -c 'python3 tests/test_schemes.py --schemes \"{algo}\" > {result_path}/log.txt 2>&1'"
            )

            try:
                subprocess.run(test_command, shell=True, check=True)
                print(f"[SUCCESS] {algo.upper()} test completed for Profile {prof_id}")
            except subprocess.CalledProcessError as err:
                print(f"[ERROR] Test failed for {algo.upper()} (Profile {prof_id}): {err}")

            metric_logs = sorted(glob.glob(f"logs/metrics_{algo}_*.csv"), key=os.path.getmtime, reverse=True)
            if metric_logs:
                newest_log = metric_logs[0]
                shutil.copy(newest_log, os.path.join(result_path, f"{algo}_cc_log.csv"))
                print(f"[INFO] Metrics file saved for {algo.upper()} (Profile {prof_id})")
            else:
                print(f"[WARNING] No metrics file found for {algo.upper()} (Profile {prof_id})")

def collect_dataframes():
    frames = []
    for prof in NET_PROFILES:
        for algo in CC_ALGOS:
            log_file = f'results/profile_{prof}/{algo}/{algo}_cc_log.csv'
            if os.path.isfile(log_file):
                df = pd.read_csv(log_file)
                df["scheme"] = algo
                df["profile"] = prof
                df["timestamp"] = list(range(len(df)))
                frames.append(df)
            else:
                print(f"[WARNING] Missing CSV file for {algo.upper()} (Profile {prof})")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def draw_throughput_plot(data):
    for prof in data['profile'].unique():
        print(f"[INFO] Generating throughput plot for Profile {prof}")
        plt.figure()
        for algo in data['scheme'].unique():
            subdata = data[(data['scheme'] == algo) & (data['profile'] == prof)]
            plt.plot(subdata['timestamp'], subdata['throughput'], label=algo)
        plt.title(f'Throughput Over Time - Profile {prof}')
        plt.xlabel('Time (s)')
        plt.ylabel('Throughput (Mbps)')
        plt.legend()
        plt.grid(True)
        plt.savefig(f'graphs/throughput_profile_{prof}.png')
        plt.close()

def draw_loss_plot(data):
    for prof in data['profile'].unique():
        print(f"[INFO] Generating loss rate plot for Profile {prof}")
        plt.figure()
        for algo in data['scheme'].unique():
            subdata = data[(data['scheme'] == algo) & (data['profile'] == prof)]
            if 'loss_rate' in subdata.columns:
                plt.plot(subdata['timestamp'], subdata['loss_rate'], label=algo)
        plt.title(f'Loss Rate Over Time - Profile {prof}')
        plt.xlabel('Time (s)')
        plt.ylabel('Loss Rate')
        plt.legend()
        plt.grid(True)
        plt.savefig(f'graphs/loss_profile_{prof}.png')
        plt.close()

def summarize_rtt(data):
    print("[INFO] Summarizing RTT statistics")
    rtt_records = []
    for prof in data['profile'].unique():
        for algo in data['scheme'].unique():
            subdata = data[(data['scheme'] == algo) & (data['profile'] == prof)]
            if not subdata.empty:
                mean_rtt = subdata['rtt'].mean()
                p95_rtt = subdata['rtt'].quantile(0.95)
                rtt_records.append((algo, prof, mean_rtt, p95_rtt))
    summary_df = pd.DataFrame(rtt_records, columns=["Scheme", "Profile", "Avg RTT", "95th RTT"])
    summary_df.to_csv("graphs/rtt_summary.csv", index=False)
    print(summary_df.to_string(index=False))

def scatter_rtt_vs_throughput(data):
    print("[INFO] Creating RTT vs Throughput scatter plot")
    plt.figure()
    for prof in data['profile'].unique():
        for algo in data['scheme'].unique():
            subdata = data[(data['scheme'] == algo) & (data['profile'] == prof)]
            if not subdata.empty:
                rtt_avg = subdata['rtt'].mean()
                tp_avg = subdata['throughput'].mean()
                plt.scatter(rtt_avg, tp_avg, label=f'{algo}-{prof}')
                plt.annotate(f'{algo}-{prof}', (rtt_avg, tp_avg))
    plt.title("Avg Throughput vs Avg RTT")
    plt.xlabel("RTT (ms)")
    plt.ylabel("Throughput (Mbps)")
    plt.grid(True)
    plt.legend()
    plt.savefig("graphs/rtt_vs_throughput.png")
    plt.close()


def bar_plot_rtt_summary(data):
    print("[INFO] Creating bar plot for RTT summary")
    rtt_records = []
    for prof in data['profile'].unique():
        for algo in data['scheme'].unique():
            subdata = data[(data['scheme'] == algo) & (data['profile'] == prof)]
            if not subdata.empty:
                mean_rtt = subdata['rtt'].mean()
                p95_rtt = subdata['rtt'].quantile(0.95)
                rtt_records.append({
                    "Scheme": algo,
                    "Profile": prof,
                    "Avg RTT": mean_rtt,
                    "95th RTT": p95_rtt
                })
    df_summary = pd.DataFrame(rtt_records)

    fig, ax = plt.subplots(figsize=(10, 6))
    width = 0.35
    schemes_profiles = [f"{row['Scheme']}-{row['Profile']}" for _, row in df_summary.iterrows()]
    x = range(len(schemes_profiles))

    ax.bar(x, df_summary["Avg RTT"], width=width, label='Avg RTT', color='skyblue')
    ax.bar([i + width for i in x], df_summary["95th RTT"], width=width, label='95th RTT', color='orange')

    ax.set_xticks([i + width/2 for i in x])
    ax.set_xticklabels(schemes_profiles, rotation=45, ha='right')
    ax.set_ylabel("RTT (ms)")
    ax.set_title("Avg vs 95th Percentile RTT by Scheme and Profile")
    ax.legend()
    ax.grid(axis='y')

    plt.tight_layout()
    plt.savefig("graphs/rtt_bar_summary.png")
    plt.close()


def orchestrate():
    print("[SETUP] Creating required directories")
    os.makedirs("graphs", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    execute_tests()

    print("[PROCESS] Collecting and processing test results")
    full_df = collect_dataframes()
    if full_df.empty:
        print("[ERROR] No data collected. Please check logs or metrics output.")
        return

    draw_throughput_plot(full_df)
    draw_loss_plot(full_df)
    summarize_rtt(full_df)
    scatter_rtt_vs_throughput(full_df)
    bar_plot_rtt_summary(full_df)


    print("[COMPLETE] All tests finished and plots saved in the 'graphs/' directory")

if __name__ == "__main__":
    orchestrate()
