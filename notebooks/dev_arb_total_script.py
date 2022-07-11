# Todos:
# check how it is possible to still save market cap from uniswap even when a trade of 80% happens
# use GraphQL to get Uniswap transactions from GRAPH in Python

import numpy as np
from liquidity_pool import LiquidityPool


uniswap_liquity_ratio = 0.5
arb_trade_boot_num = 10
large_sell_ratio = 0.01
boot_token_num = 50000
amplification=None,
arb_price_tolerance=0.03
large_uniswap_trade=True
token_labels = ['Boot', 'USDC']

amplification = [85, 0.0001]
# amplification = [0.00001, 0.00001]

# equal amount Boot and USDC, price = $1 per Boot
initial_token_amounts = np.array([boot_token_num, boot_token_num])

uniswap_token_amounts = uniswap_liquity_ratio * initial_token_amounts
customswap_token_amounts = initial_token_amounts - uniswap_token_amounts

lp_uniswap = LiquidityPool(token_labels, uniswap_token_amounts.copy(), fee_ratio=0, pricing_method='uniswap')
lp_customswap = LiquidityPool(token_labels, customswap_token_amounts, fee_ratio=0,
                              pricing_method='customswap', amplification=amplification,
                              promoted_token_label='Boot')

# lp_customswap = LiquidityPool(token_labels, customswap_token_amounts.copy(), fee_ratio=0, pricing_method='uniswap')



# Perform one large sell trade of Boot token in Uniswap or Customswap pool
large_sell_num_tokens = initial_token_amounts[0] * large_sell_ratio

uniswap_boot_tokens = []
customswap_boot_tokens = []

customswap_token_ratios = []
uniswap_token_ratios = []

uniswap_boot_tokens.append(lp_uniswap._token_amounts[0])
customswap_boot_tokens.append(lp_customswap._token_amounts[0])

if large_uniswap_trade:
    # large sale trade in Uniswap
    lp_uniswap.get_price(payment_token_label='USDC',
                         requested_token_label='Boot')

    lp_uniswap.exchange(payment_token_label='Boot',
                        requested_token_label='USDC',
                        payment_token_amount=large_sell_num_tokens)

    lp_uniswap.get_price(payment_token_label='USDC',
                         requested_token_label='Boot')
else:  # large sale trade in Customswap
    lp_customswap.get_price(payment_token_label='USDC',
                            requested_token_label='Boot')

    lp_customswap.exchange(payment_token_label='Boot',
                           requested_token_label='USDC',
                           payment_token_amount=large_sell_num_tokens)

    lp_customswap.get_price(payment_token_label='USDC',
                            requested_token_label='Boot')

# arbitrage simulation between the two pools until the price become very similar (to ~3% of each other)

uniswap_prices_before_arb = []
customswap_prices_before_arb = []
received_boot_amounts = []
received_usdc_amounts = []
uniswap_prices_after_arb = []
customswap_prices_after_arb = []
arbBootGains = []


uniswap_boot_tokens.append(lp_uniswap._token_amounts[0])
customswap_boot_tokens.append(lp_customswap._token_amounts[0])

while len(uniswap_prices_after_arb) == 0 or len(customswap_prices_after_arb) == 0 or \
        abs(customswap_prices_before_arb[-1] - uniswap_prices_before_arb[-1]) / \
        ((customswap_prices_before_arb[-1] + uniswap_prices_before_arb[-1]) / 2) > arb_price_tolerance:

    uniswap_prices_before_arb.append(lp_uniswap.get_price(payment_token_label='USDC',
                                                          requested_token_label='Boot'))

    customswap_prices_before_arb.append(lp_customswap.get_price(payment_token_label='USDC',
                                                                requested_token_label='Boot'))

    # if price of Boot token in Customswap is higher, then sell some Boot there, then use the USDC money to
    # buy token on Uniswap (increasing price)
    if customswap_prices_before_arb[-1] > uniswap_prices_before_arb[-1]:

        received_usdc_amount = lp_customswap.exchange(payment_token_label='Boot',
                                                      requested_token_label='USDC',
                                                      payment_token_amount=arb_trade_boot_num)

        received_boot_amount = lp_uniswap.exchange(payment_token_label='USDC',
                                                   requested_token_label='Boot',
                                                   payment_token_amount=received_usdc_amount)

        arbBootGains.append(received_boot_amount - arb_trade_boot_num)

        uniswap_boot_tokens.append(lp_uniswap._token_amounts[0])
        customswap_boot_tokens.append(lp_customswap._token_amounts[0])


        # if price of Boot token in Uniswap is higher, then sell some Boot there, then use the USDC money to
    # buy token on Customswap (increasing price)
    elif customswap_prices_before_arb[-1] < uniswap_prices_before_arb[-1]:
        received_usdc_amount = lp_uniswap.exchange(payment_token_label='Boot',
                                                   requested_token_label='USDC',
                                                   payment_token_amount=arb_trade_boot_num)

        received_boot_amount = lp_customswap.exchange(payment_token_label='USDC',
                                                      requested_token_label='Boot',
                                                      payment_token_amount=received_usdc_amount)

        arbBootGains.append(received_boot_amount - arb_trade_boot_num)

        uniswap_boot_tokens.append(lp_uniswap._token_amounts[0])
        customswap_boot_tokens.append(lp_customswap._token_amounts[0])

    received_boot_amounts.append(received_boot_amount)
    received_usdc_amounts.append(received_usdc_amount)

    customswap_token_ratios.append(lp_customswap._token_amounts[1] / lp_customswap._token_amounts[0])
    uniswap_token_ratios.append(lp_uniswap._token_amounts[1] / lp_uniswap._token_amounts[0])

    uniswap_prices_after_arb.append(lp_uniswap.get_price(payment_token_label='USDC',
                                                         requested_token_label='Boot'))

    customswap_prices_after_arb.append(lp_customswap.get_price(payment_token_label='USDC', requested_token_label='Boot'))

print('Uniswap price:', lp_uniswap.get_price(payment_token_label='USDC', requested_token_label='Boot'))
print('Customswap price:', lp_uniswap.get_price(payment_token_label='USDC', requested_token_label='Boot'))

print('Ratio of arbBootGains:', np.sum(arbBootGains) / ((large_sell_ratio + 1) * boot_token_num))


# %%


# import matplotlib.pyplot as plt
# plt.figure(figsize=(20, 10))
#
# plt.plot(arbBootGains, 'o-')
# plt.plot(np.cumsum(arbBootGains), 'o-')
# plt.xlabel('Arb step')
# plt.xlabel('Book tokens')
# plt.show()



import matplotlib.pyplot as plt
# plt.figure(figsize=(20, 10))

f, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, sharex=False,
                                           figsize=(20, 12))

ax1.plot(np.cumsum(arbBootGains))
ax1.legend(['Cumulative Boot tokens drained by arb'])

ax2.plot(uniswap_boot_tokens, 'o-')
ax2.plot(customswap_boot_tokens, 'o-')
ax2.plot(np.array(uniswap_boot_tokens) + np.array(customswap_boot_tokens), 'o-')

ax2.legend(['uniswap boot tokens', 'customswap boot tokens', 'total boot tokens'])

ax3.plot(uniswap_token_ratios)
ax3.plot(customswap_token_ratios)
ax3.legend(['uniswap token ratios', 'customswap token ratios'])

ax4.plot(uniswap_prices_after_arb)
ax4.plot(customswap_prices_after_arb)
ax4.legend(['uniswap price', 'customswap price'])



plt.show()










