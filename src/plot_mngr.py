import numpy as np
from os import PathLike
from pathlib import Path
import matplotlib.pyplot as plt

def plot_pie(nums: list[float], fig_path: PathLike, labels: list[str] = None) -> None:
    y = np.array(nums)
    if labels:
        plt.pie(y, labels=labels)
    else:
        plt.pie(y)
    plt.savefig(fig_path)
    plt.show()

def plot_bar(nums: list[float], fig_path: PathLike, labels: list[str] = None) -> None:
    y = np.array(nums)
    x = np.arange(len(y))
    if labels:
        plt.bar(x, y, tick_label=labels)
    else:
        plt.bar(x, y)
    plt.axhline(0, color='black', linewidth=0.8)
    plt.savefig(fig_path)
    plt.show()

def plot_monthly_stocks(fig_path: PathLike, data_dict: dict,
                        entry_points: dict, **kwargs) -> list[PathLike]:
    Path(fig_path).parent.mkdir(parents=True, exist_ok=True)
    figs_paths = []
    for elm in data_dict:
        x = np.arange(len(data_dict[elm].keys()))
        names = list(data_dict[elm].keys())
        y_list = []
        for i in data_dict[elm].values():
            y_list.append(i['price'])
        y = np.array(y_list)
        fig, ax = plt.subplots(1, 1, figsize=(12, 6))
        ax.plot(x, y, marker='o', linestyle='-', color='b')
        ax.set_xticks(x)
        ax.set_xticklabels(names)
        ax.set_title(elm.upper())
        figs_paths.append(fig_path.replace('.png', f'_{elm.lower()}.png'))
        fig.savefig(fig_path.replace('.png', f'_{elm.lower()}.png'))
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    colors = plt.cm.get_cmap('tab10', len(data_dict))
    for idx, elm in enumerate(data_dict):
        entry = entry_points.get(elm)
        if entry:
            entry_x = names.index(entry)
            base_price = list(data_dict[elm].values())[0]['price']
            entry_y = (data_dict[elm][entry]['price'] / base_price) * 100
            ax.plot(entry_x, entry_y, marker='o', markersize=10, color='black')
        x = np.arange(len(data_dict[elm].keys()))
        names = list(data_dict[elm].keys())
        y_list = []
        for i in data_dict[elm].values():
            if len(y_list) == 0:
                base_price = i['price']
            y_list.append((i['price'] / base_price) * 100)
        y = np.array(y_list)
        ax.plot(x, y, marker='o', linestyle='-', label=elm.upper(), color=colors(idx))
    ax.grid(True)
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_title('Combined Monthly Stocks')
    ax.legend()
    figs_paths.append(fig_path)
    fig.savefig(fig_path)
    if kwargs.get('show', False):
        plt.show()
    return figs_paths

def plot_combined(fig_path: PathLike, nums_pie: list[float], nums_bar: list[float],
                  nums_points: list[float], nums_points_1: list[float],
                  labels_pie: list[str] = None, labels_bar: list[str] = None,
                  labels_points: list[str] = None, labels_points_1: list[str] = None,
                  **kwargs) -> list[PathLike]:
    Path(fig_path).parent.mkdir(parents=True, exist_ok=True)
    figs_paths = []
    y1 = np.array(nums_pie)
    y2 = np.array(nums_bar)
    y3 = np.array(nums_points)
    y4 = np.array([100 * num_point / nums_points_1[-1] for num_point in nums_points_1])
    fig1, ax1 = plt.subplots(1, 1, figsize=(12, 6))
    fig2, ax2 = plt.subplots(1, 1, figsize=(12, 6))
    fig3, ax3 = plt.subplots(1, 1, figsize=(12, 6))
    fig4, ax4 = plt.subplots(1, 1, figsize=(12, 6))
    ax1.pie(y1, labels=labels_pie, autopct='%1.1f%%')
    ax1.set_title(kwargs.get('pie_title', 'Pie Chart'))
    x2 = np.arange(len(y2))
    ax2.bar(x2, y2, tick_label=labels_bar)
    ax2.axhline(0, color='black', linewidth=0.8)
    ax2.set_title(kwargs.get('bar_title', 'Bar Chart'))
    ax2.grid(True)
    x3 = np.arange(len(nums_points))
    ax3.plot(x3, y3, marker='o', linestyle='-', color='r')
    ax3.set_xticks(x3)
    ax3.set_xticklabels(labels_points)
    ax3.set_title(kwargs.get('points_title', 'Points Chart'))
    ax3.grid(True)
    x4 = np.arange(len(nums_points_1))
    ax4.plot(x4, y4, marker='o', linestyle='-', color='b')
    ax4.set_xticks(x4)
    ax4.set_xticklabels(labels_points_1)
    ax4.set_title(kwargs.get('points1_title', 'Points 1 Chart'))
    ax4.grid(True)
    fig1_name = fig_path.replace('.png', f'_pie_{kwargs.get("pie_title", "chart").lower().replace(" ", "_")}.png')
    fig2_name = fig_path.replace('.png', f'_bar_{kwargs.get("bar_title", "chart").lower().replace(" ", "_")}.png')
    fig3_name = fig_path.replace('.png', f'_points_{kwargs.get("points_title", "chart").lower().replace(" ", "_")}.png')
    fig4_name = fig_path.replace('.png', f'_points_{kwargs.get("points1_title", "chart").lower().replace(" ", "_")}.png')
    fig1.savefig(fig1_name)
    fig2.savefig(fig2_name)
    fig3.savefig(fig3_name)
    fig4.savefig(fig4_name)
    figs_paths.append(fig1_name)
    figs_paths.append(fig2_name)
    figs_paths.append(fig3_name)
    figs_paths.append(fig4_name)
    if kwargs.get('show', False):
        plt.show()
    return figs_paths
