from os import PathLike
from pathlib import Path
from typing import Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter, MaxNLocator

from src.portfolio_mngr import convert_date_to_short_str, history_key_date

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


def use_date_axis(ax) -> None:
    """Ticks a date x axis at a readable density, for month (lite) or daily (full) history."""
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))


def point_marker(points: list) -> Optional[str]:
    """A marker per point, unless there are so many (daily history) that they merge."""
    return 'o' if len(points) <= 100 else None


def plot_monthly_stocks(
    fig_path: PathLike, data_dict: dict, entry_points: dict, **kwargs
) -> list[PathLike]:
    Path(fig_path).parent.mkdir(parents=True, exist_ok=True)
    figs_paths = []
    for elm in data_dict:
        days = [history_key_date(key) for key in data_dict[elm]]
        prices = [point['price'] for point in data_dict[elm].values()]
        fig, ax = plt.subplots(1, 1, figsize=(12, 6))
        ax.plot(days, prices, marker=point_marker(days), linestyle='-', color='b')
        use_date_axis(ax)
        ax.set_title(elm.upper())
        figs_paths.append(fig_path.replace('.png', f'_{elm.lower()}.png'))
        fig.savefig(fig_path.replace('.png', f'_{elm.lower()}.png'))
        plt.close(fig)
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    colors = plt.cm.get_cmap('tab10', len(data_dict))
    for idx, elm in enumerate(data_dict):
        # On a date axis, series with different dates (a later listing, other trading days)
        # line up.
        days = [history_key_date(key) for key in data_dict[elm]]
        prices = [point['price'] for point in data_dict[elm].values()]
        if not prices:
            continue
        y = [price / prices[0] * 100 for price in prices]
        ax.plot(
            days, y, marker=point_marker(days), linestyle='-', label=elm.upper(), color=colors(idx)
        )
        # The entry point is a month key; mark the series' first point in that month.
        entry_x = next(
            (
                i
                for i, day in enumerate(days)
                if convert_date_to_short_str(date=day) == entry_points.get(elm)
            ),
            None,
        )
        if entry_x is not None:
            ax.plot(days[entry_x], y[entry_x], marker='o', markersize=10, color='black')
    use_date_axis(ax)
    ax.grid(True)
    ax.set_title('Combined Monthly Stocks')
    ax.legend()
    figs_paths.append(fig_path)
    fig.savefig(fig_path)
    if kwargs.get('show', False):
        plt.show()
    plt.close(fig)
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
    # The points are labelled with month keys; one tick label per month overlaps after a year.
    x3 = [history_key_date(month) for month in labels_points]
    ax3.plot(x3, y3, marker='o', linestyle='-', color='r')
    use_date_axis(ax3)
    ax3.set_title(kwargs.get('points_title', 'Points Chart'))
    ax3.grid(True)
    x4 = [history_key_date(month) for month in labels_points_1]
    ax4.plot(x4, y4, marker='o', linestyle='-', color='b')
    use_date_axis(ax4)
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
    for fig in (fig1, fig2, fig3, fig4):
        plt.close(fig)
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
