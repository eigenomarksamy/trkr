from os import PathLike
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter, MaxNLocator

# Categorical slots 1-3 of the validated dataviz palette, in fixed order.
SERIES_COLORS = ['#2a78d6', '#eb6834', '#1baf7a']
TEXT_PRIMARY = '#0b0b0b'
TEXT_SECONDARY = '#52514e'
GRID_COLOR = '#e4e3df'


def format_compact(value: float) -> str:
    for threshold, suffix in ((1e9, 'B'), (1e6, 'M'), (1e3, 'K')):
        if abs(value) >= threshold:
            return f'{value / threshold:.3g}{suffix}'
    return f'{value:.0f}'


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


def plot_monthly_stocks(
    fig_path: PathLike, data_dict: dict, entry_points: dict, **kwargs
) -> list[PathLike]:
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


def plot_combined(
    fig_path: PathLike,
    nums_pie: list[float],
    nums_bar: list[float],
    nums_points: list[float],
    nums_points_1: list[float],
    labels_pie: list[str] = None,
    labels_bar: list[str] = None,
    labels_points: list[str] = None,
    labels_points_1: list[str] = None,
    **kwargs,
) -> list[PathLike]:
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
    fig1_name = fig_path.replace(
        '.png', f'_pie_{kwargs.get("pie_title", "chart").lower().replace(" ", "_")}.png'
    )
    fig2_name = fig_path.replace(
        '.png', f'_bar_{kwargs.get("bar_title", "chart").lower().replace(" ", "_")}.png'
    )
    fig3_name = fig_path.replace(
        '.png', f'_points_{kwargs.get("points_title", "chart").lower().replace(" ", "_")}.png'
    )
    fig4_name = fig_path.replace(
        '.png', f'_points_{kwargs.get("points1_title", "chart").lower().replace(" ", "_")}.png'
    )
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


def plot_projection(
    fig_path: PathLike, years: list[int], birth_year: int, series: dict[str, list[float]]
) -> PathLike:
    """One line per series (at most three), each labelled in the legend with its final value."""
    Path(fig_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    for color, (name, values) in zip(SERIES_COLORS, series.items(), strict=False):
        ax.plot(
            years,
            values,
            color=color,
            linewidth=2,
            solid_joinstyle='round',
            solid_capstyle='round',
            label=f'{name}: {format_compact(values[-1])}',
        )
        ax.plot(
            years[-1],
            values[-1],
            marker='o',
            markersize=8,
            color=color,
            markeredgecolor='white',
            markeredgewidth=2,
        )
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda year, _: f'{year:.0f}\nage {year - birth_year:.0f}')
    )
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: format_compact(value)))
    if min(min(values) for values in series.values()) >= 0:
        ax.set_ylim(bottom=0)
    ax.grid(True, axis='y', color=GRID_COLOR, linewidth=1)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GRID_COLOR)
    ax.tick_params(colors=TEXT_SECONDARY, length=0)
    ax.set_title('Net-worth Projection', loc='left', color=TEXT_PRIMARY)
    legend = ax.legend(frameon=False, loc='upper left')
    for text in legend.get_texts():
        text.set_color(TEXT_SECONDARY)
    fig.savefig(fig_path)
    plt.close(fig)
    return fig_path
