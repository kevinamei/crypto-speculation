# %%
''' 
Build Figure fig:icp_example 
'''

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

matplotlib.rcParams['font.family'] = 'Serif'

FONT_SIZE = 18
TICK_SIZE = 14         
WINDOW_MONTHS = 60
DAYS_PER_MONTH = 30     


# %%
''' ---------- inputs ---------- '''
''' collected from ICP dashboard '''
prices_df = pd.read_parquet('price_data.parquet')
prices_df['date'] = pd.to_datetime(prices_df['date'])
prices_df2 = prices_df.loc[prices_df['market_cap'] > 0].sort_values('date')

icp_df = pd.read_parquet('transaction_volume.parquet')
icp_df['date'] = pd.to_datetime(icp_df['date'])
icp_df['txn_count'] = icp_df['count'].astype(int)

''' from https://etherscan.io/chart/tx '''
eth_df = pd.read_csv('EthTxGrowth.csv')
eth_df['date'] = pd.to_datetime(eth_df['Date(UTC)'])
eth_df = eth_df.groupby(['date'])['Value'].sum().reset_index()
eth_df['txn_count'] = eth_df['Value'].astype(int)

# %%
''' ---------- align both chains on months since their own launch ---------- '''

for df in (icp_df, eth_df):
    df['num_days'] = (df['date'] - df['date'].min()).dt.days
    df['num_months'] = df['num_days'] / DAYS_PER_MONTH

window_days = WINDOW_MONTHS * DAYS_PER_MONTH

for name, df in (('ICP', icp_df), ('Ethereum', eth_df)):
    assert df['num_days'].max() >= window_days, (
        f'{name} has only {df["num_days"].max()} days, '
        f'need {window_days} for a {WINDOW_MONTHS}-month window')

plot_df = eth_df.loc[eth_df['num_days'] <= window_days].copy()
plot_df = plot_df.merge(icp_df[['num_days', 'txn_count']], how='left',
                        on='num_days', suffixes=('_eth', '_icp'))

# %%
''' legend labels: the calendar span each series actually covers in the window '''

def span_label(name, df):
    ''' The x-axis is in months, so the legend is labelled in whole calendar
        months from launch. Note the plotted window is WINDOW_MONTHS * 30 days,
        which runs ~26 days short of 60 true calendar months; the label follows
        the axis rather than that 26-day shortfall. '''
    start = df['date'].min()
    end = start.to_period('M') + WINDOW_MONTHS
    return f'{name} ({start:%b %Y} - {end.to_timestamp():%b %Y})'

icp_label = span_label('Internet Computer Protocol', icp_df)
eth_label = span_label('Ethereum', eth_df)
print(icp_label)
print(eth_label)

# %%
''' ---------- two panel plot ---------- '''

plt.rc('font', family='serif')

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12))

ax1.plot(prices_df2['date'], prices_df2['market_cap'] / 1_000_000_000)
ax1.set_xlabel('Date', fontsize=FONT_SIZE)
ax1.set_ylabel('Market Cap ($B)', fontsize=FONT_SIZE)
# ax1.set_title('Panel A: Market Capitalization of Internet Computer Protocol (ICP)', fontsize=FONT_SIZE)
ax1.set_title('(a) Market Capitalization of Internet Computer Protocol (ICP)', fontsize=FONT_SIZE)

''' right edge = start of the month after the last observation '''
x_hi = (prices_df2['date'].max().to_period('M') + 1).to_timestamp()
ax1.set_xlim(pd.to_datetime('2021-05-01'), x_hi)
ax1.xaxis.set_major_locator(mdates.YearLocator())
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax1.set_ylim(0, ax1.get_ylim()[1])

''' create space between the two plots '''
fig.subplots_adjust(hspace=0.25)

ax2.plot(plot_df['num_months'], plot_df['txn_count_icp'] / 1_000, label=icp_label)
ax2.plot(plot_df['num_months'], plot_df['txn_count_eth'] / 1_000, label=eth_label,
         color='gray', linestyle='--')
ax2.set_xlabel('Months since launch', fontsize=FONT_SIZE)
ax2.set_ylabel('Number of daily transactions (000s)', fontsize=FONT_SIZE)
# ax2.set_title('Panel B: Number of Daily Transactions, by Number of Months Since Launch', fontsize=FONT_SIZE)
ax2.set_title('(b) Number of Daily Transactions, by Number of Months Since Launch', fontsize=FONT_SIZE)

ax2.legend(loc='upper left', fontsize=FONT_SIZE)
ax2.set_xticks(range(0, WINDOW_MONTHS + 1, 12))
ax2.set_xlim(0, WINDOW_MONTHS)
ax2.set_ylim(0, ax2.get_ylim()[1])

for ax in (ax1, ax2):
    ax.tick_params(axis='both', labelsize=TICK_SIZE)

fig.savefig('icp_example.png', dpi=300, bbox_inches='tight')
