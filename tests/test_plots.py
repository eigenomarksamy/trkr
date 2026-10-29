import matplotlib.pyplot as plt
import pytest

from src.plot_mngr import plot_combined, plot_monthly_stocks


@pytest.fixture(autouse=True)
def no_open_figures():
    plt.close('all')
    yield
    plt.close('all')


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
