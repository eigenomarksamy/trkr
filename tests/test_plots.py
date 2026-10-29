import matplotlib.pyplot as plt
import pytest
from matplotlib.figure import Figure

from src.plot_mngr import plot_combined, plot_monthly_stocks


@pytest.fixture(autouse=True)
def no_open_figures():
    plt.close('all')
    yield
    plt.close('all')


@pytest.fixture
def saved_figures(monkeypatch) -> dict:
    """Keeps each figure instead of writing it, by path."""
    saved = {}

    def savefig(fig, path, *args, **kwargs):
        saved[str(path)] = fig

    monkeypatch.setattr(Figure, 'savefig', savefig)
    return saved


def test_entry_points_sit_on_their_own_series(tmp_path, saved_figures):
    fig_path = f'{tmp_path.as_posix()}/history.png'
    plot_monthly_stocks(
        fig_path=fig_path,
        data_dict={
            'AAA': history({'jan24': 10, 'feb24': 20, 'mar24': 40}),
            # Listed a month later, so its history is shorter than AAA's.
            'BBB': history({'feb24': 5, 'mar24': 10}),
        },
        entry_points={'AAA': 'feb24', 'BBB': 'feb24'},
    )
    lines = saved_figures[fig_path].axes[0].get_lines()
    series = {line.get_label(): line for line in lines if line.get_markersize() != 10}
    markers = [line for line in lines if line.get_markersize() == 10]

    def points(line):
        return list(zip(line.get_xdata(), line.get_ydata(), strict=True))

    # Feb 2024 is AAA's second point and BBB's first, and both share an x position.
    assert points(markers[0]) == [points(series['AAA'])[1]]
    assert points(markers[1]) == [points(series['BBB'])[0]]
    assert points(markers[0])[0][0] == points(markers[1])[0][0]
    # Each series is indexed to its first price.
    assert [y for _, y in points(series['AAA'])] == [100, 200, 400]
    assert [y for _, y in points(series['BBB'])] == [100, 200]


def test_full_history_entry_points_are_the_first_day_of_the_month(tmp_path, saved_figures):
    fig_path = f'{tmp_path.as_posix()}/history.png'
    plot_monthly_stocks(
        fig_path=fig_path,
        data_dict={'AAA': history({'2024-01-30': 10, '2024-02-01': 11, '2024-02-02': 12})},
        entry_points={'AAA': 'feb24'},
    )
    lines = saved_figures[fig_path].axes[0].get_lines()
    marker = [line for line in lines if line.get_markersize() == 10][0]
    assert marker.get_ydata()[0] == pytest.approx(110)


def history(prices: dict) -> dict:
    return {key: {'price': price} for key, price in prices.items()}


def test_plots_close_their_figures(tmp_path):
    # pyplot keeps every figure until it is closed: a warning past 20, and memory in long runs.
    plot_monthly_stocks(
        fig_path=f'{tmp_path.as_posix()}/stocks/history.png',
        data_dict={
            'AAA': history({'jan24': 10, 'feb24': 11}),
            'BBB': history({'jan24': 20, 'feb24': 19}),
        },
        entry_points={'AAA': 'jan24', 'BBB': 'feb24'},
    )
    plot_combined(
        fig_path=f'{tmp_path.as_posix()}/gen_stats.png',
        nums_pie=[60, 40],
        nums_bar=[10, -5, 4],
        nums_points=[70, 30],
        nums_points_1=[100, 200],
        labels_pie=['AAA', 'BBB'],
        labels_bar=['AAA', 'BBB', 'Total'],
        labels_points=['jan24', 'feb24'],
        labels_points_1=['jan24', 'feb24'],
        points_title='Spending Per Month',
        points1_title='Valuation Percent',
        pie_title='Spending Percent',
        bar_title='Profit Percent',
    )
    assert plt.get_fignums() == []
    assert len(list(tmp_path.rglob('*.png'))) == 7


def test_full_history_charts_keep_their_ticks_readable(tmp_path, saved_figures):
    fig_path = f'{tmp_path.as_posix()}/history.png'
    days = [f'2024-{month:02}-{day:02}' for month in range(1, 13) for day in range(1, 29)]
    plot_monthly_stocks(
        fig_path=fig_path,
        data_dict={'AAA': history({day: 10 + i for i, day in enumerate(days)})},
        entry_points={'AAA': 'mar24'},
    )
    for path in (fig_path, fig_path.replace('.png', '_aaa.png')):
        ax = saved_figures[path].axes[0]
        # One label per day used to be 336 labels.
        assert len(ax.get_xticks()) <= 15
