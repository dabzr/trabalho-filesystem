import sys
import time
import csv
import os
import random
import statistics as stats
import matplotlib.pyplot as plt

from chainfilesystem import ChainFileSystem
from inodefilesystem import INodeFileSystem

def timeit(fn):
    """Return wall‑clock runtime of *fn()* in seconds."""
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def make_random_names(prefix: str, n: int):
    """Generate *n* unique random identifiers with a given prefix."""
    return [f"{prefix}{random.getrandbits(48):012x}" for _ in range(n)]


def one_pass(fs_class, dir_names, file_names, block_size=512):
    """Run one full operation set on a freshly‑created filesystem."""
    num_blocks = 4096
    fs = fs_class(num_blocks=num_blocks, block_size=block_size)

    dir_create = timeit(lambda: [fs.make_directory([name]) for name in dir_names])
    dir_delete = timeit(lambda: [fs.remove_directory([name]) for name in dir_names])

    file_create = timeit(lambda: [fs.make_file([name, "hello world"]) for name in file_names])
    file_delete = timeit(lambda: [fs.remove_file([name]) for name in file_names])

    large_blob = "x" * (block_size * 4)
    large_write = timeit(lambda: fs.make_file(["large.txt", large_blob]))
    large_read  = timeit(lambda: fs._cat(["large.txt"]))

    return {
        "dir_create_time":   dir_create,
        "dir_delete_time":   dir_delete,
        "file_create_time":  file_create,
        "file_delete_time":  file_delete,
        "large_write_time":  large_write,
        "large_read_time":   large_read,
    }


def run_benchmarks(op_counts, passes: int = 5):
    fs_classes = [ChainFileSystem, INodeFileSystem]
    metrics = [
        "dir_create_time", "dir_delete_time",
        "file_create_time", "file_delete_time",
        "large_write_time", "large_read_time",
    ]

    # Prepare output directory & CSV
    outdir = "benchmark_stats"
    os.makedirs(outdir, exist_ok=True)
    csv_path = os.path.join(outdir, "benchmark_stats.csv")

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["fs_type", "num_ops", "metric", "mean", "std"])

        # Organise data for plotting
        means = {cls.__name__: {m: [] for m in metrics} for cls in fs_classes}
        stds  = {cls.__name__: {m: [] for m in metrics} for cls in fs_classes}

        # Iterate over workload sizes
        for n in op_counts:
            print(f"\n▶️  {n} ops × {passes} passes")

            # Pre‑generate random name lists for fairness (same lists for both FSes each pass)
            dir_name_sets  = [make_random_names("dir_", n)  for _ in range(passes)]
            file_name_sets = [make_random_names("file_", n) for _ in range(passes)]

            for cls in fs_classes:
                # Collect timings from each pass
                samples = {m: [] for m in metrics}

                for p in range(passes):
                    res = one_pass(cls, dir_name_sets[p], file_name_sets[p])
                    for m in metrics:
                        samples[m].append(res[m])

                # Compute mean & std and write CSV rows
                for m in metrics:
                    mu = stats.mean(samples[m])
                    sigma = stats.stdev(samples[m]) if passes > 1 else 0.0
                    writer.writerow([cls.__name__, n, m, f"{mu:.6f}", f"{sigma:.6f}"])

                    means[cls.__name__][m].append(mu)
                    stds[cls.__name__][m].append(sigma)

                print(f"  {cls.__name__}: OK")

    print(f"\nCSV salvo em {csv_path}")

    for metric in metrics:
        plt.figure()
        for cls in fs_classes:
            mu  = means[cls.__name__][metric]
            sig = stds[cls.__name__][metric]
            plt.errorbar(op_counts, mu, yerr=sig, marker="o", capsize=4, label=cls.__name__)
        plt.title(f"{metric} – média ± desvio‑padrão (n={passes})")
        plt.xlabel("Nº de operações")
        plt.ylabel("Tempo (segundos)")
        plt.legend()
        plt.tight_layout()
        img_path = os.path.join(outdir, f"metric_{metric}.png")
        plt.savefig(img_path)
        print(f"  📊  Plot salvo: {img_path}")
        plt.close()

    print("\n✅  Benchmark completo!")


def main():
    # Parse CLI: allow custom op counts
    if len(sys.argv) > 1:
        try:
            op_counts = [int(x) for x in sys.argv[1:]]
        except ValueError:
            print("Uso: python benchmark.py [num_ops1 num_ops2 ...]")
            return
    else:
        op_counts = [10, 20, 40, 80, 160, 320]

    run_benchmarks(op_counts, passes=5)


if __name__ == "__main__":
    main()
