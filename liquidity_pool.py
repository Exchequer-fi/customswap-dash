import src.utils as ut
from typing import List, Union
import numpy as np

VERY_SMALL_AMOUNT = 1e-1
UNISWAP_AMPLIFICATION = 0.00001


class LiquidityPool:
    # A liquidity pool with one of several types of pricing strategy (UniSwap, StableSwap, CustomSwap)

    def __init__(self, token_labels: List[str], token_initial_amounts: List[float], fee_ratio: float,
                 pricing_method: str, amplification: Union[float, List[float]] = UNISWAP_AMPLIFICATION,
                 promoted_token_label: str = None):
        """

        :param token_labels: list of strings indicating token names, e.g. ETH, USDC
        :param token_initial_amounts: amounts of tokens, same order as labels, e.g. 10.5 ETH, 1000 UDSC
        :param fee_ratio: fee ratio, e.g. 0.03
        :param pricing_method: type of method used for pool pricing. One of {'uniswap', 'stableswap', 'customswap'}
        :param amplification: amplification factor(s) used in 'stableswap' and 'customswap' methods. For
                              'stableswap' this would be a single number. For 'customswap' this shodul be a list of
                              two numbers.
        :param promoted_token_label: token label for which customswap reduces initial price decrease.
        :param target_price used in 'customswap' method.
        """
        self.token_labels = token_labels

        self._token_amounts = token_initial_amounts
        self._fee_ratio = fee_ratio
        self._pricing_method = pricing_method
        self._amplification = amplification
        self.amplification_transition_ratio = 1  # ratio of tokens at which A switches
        self._last_amplification = None  # the
        self._promoted_token_label = promoted_token_label# amplification factor used to calculate the last price

        # maps token labels to integer ids
        self._token_id = {}
        for i, label in enumerate(token_labels):
            self._token_id[label] = i

        # normalize token amounts at formation to both be 1
        self.token_amount_scales = token_initial_amounts
        self._token_initial_amounts = np.ones(len(token_initial_amounts))

    def get_requested_token_amount(self, payment_token_label, requested_token_label, payment_token_amount,
                                   fee_ratio):
        """
        Compute how much of the requested token will be given for a certain amount of payment token.
        :param payment_token_label: payment token label
        :param requested_token_label: requested token label
        :param payment_token_amount: payment token amount
        :param fee_ratio: fee ratio, e.g. 0.03
        :return: the amount of requested token provided to the user (swapped with payment token)
        """

        payment_token_index = self._token_id[payment_token_label]
        requested_token_index = self._token_id[requested_token_label]

        if self._pricing_method == 'stableswap':
            self._last_amplification = self._amplification
            requested_token_amount_afterwards = ut.curve_get_y(payment_token_index, requested_token_index,
                                                    self._token_amounts[payment_token_index] + payment_token_amount,
                                                    self._token_amounts, self._last_amplification)
        elif self._pricing_method == 'uniswap':
            self._last_amplification = UNISWAP_AMPLIFICATION
            requested_token_amount_afterwards = ut.curve_get_y(payment_token_index, requested_token_index,
                                                    self._token_amounts[payment_token_index] + payment_token_amount,
                                                    self._token_amounts, self._last_amplification)
        elif self._pricing_method == 'customswap':

            # - Determine the correct A by comparing xp[0] and xp[1].
            # - Calculate starting D.
            # - Calculate y given A and D
            # - Calculate xp2, being the the balances after the trade
            # - Compare xp2[0] and xp2[1] and determine the target A
            # - If A changed, calculate y again given A' and D

            promoted_token_index = self._token_id[self._promoted_token_label]
            non_promoted_token_index = list((set([0, 1]) - set([promoted_token_index])))[0]

            if self._token_amounts[promoted_token_index] / self._token_amounts[non_promoted_token_index] > \
                    self.amplification_transition_ratio:
                # when too much of the promoted token is available,
                # (slow price decrease, high amplification, more like StableSwap)
                potential_amplification = self._amplification[0]
            else:
                # when less of the promoted token is available, use UniSwap like curve
                # (faster price increase, low amplification)
                potential_amplification = self._amplification[1]

            requested_token_amount = ut.curve_get_y(payment_token_index, requested_token_index,
                        self._token_amounts[payment_token_index] + payment_token_amount,
                        self._token_amounts, potential_amplification)

            # check if the condition for choosing the amplification factor still exists
            potential_token_amounts = self._token_amounts.copy()
            potential_token_amounts[payment_token_index] += payment_token_amount
            potential_token_amounts[requested_token_index] = requested_token_amount

            if potential_token_amounts[promoted_token_index] / potential_token_amounts[non_promoted_token_index] > \
                    self.amplification_transition_ratio:
                self._last_amplification = self._amplification[0]
            else:
                self._last_amplification = self._amplification[-1]

            if self._last_amplification != potential_amplification:
                requested_token_amount_afterwards = ut.curve_get_y(payment_token_index, requested_token_index,
                                                                   self._token_amounts[payment_token_index] + payment_token_amount,
                                                                   self._token_amounts, self._last_amplification)
            else:
                requested_token_amount_afterwards = potential_token_amounts[requested_token_index]
        else:
            raise ValueError('pricing_method not recognized')

        returned_token_amount = self._token_amounts[requested_token_index] - requested_token_amount_afterwards
        fee = returned_token_amount * fee_ratio
        returned_token_amount = returned_token_amount - fee
        return returned_token_amount

    def get_last_amplification(self):
        return self._last_amplification

    def get_price(self, payment_token_label, requested_token_label, payment_token_amount=VERY_SMALL_AMOUNT):
        """
        Compute token price for payment of a very small amount of the payment token.
        :param payment_token_label: payment token label
        :param requested_token_label: requested token label
        :param payment_token_amount: payment token amount
        :return: the price, as how much of requested token will be provided for per unit of payment token.
        """

        price = payment_token_amount / self.get_requested_token_amount(payment_token_label, requested_token_label, payment_token_amount,
                                                fee_ratio=0)

        return price

    def exchange(self, payment_token_label, requested_token_label, payment_token_amount):
        """
        Swap payment token with requested token.
        :param payment_token_label: payment token label
        :param requested_token_label: requested token label
        :param payment_token_amount: payment token amount
        :return: the amount of requested token sent back to the user.
        """

        returned_token_amount = self.get_requested_token_amount(payment_token_label, requested_token_label,
                                                                payment_token_amount, fee_ratio=self._fee_ratio)

        payment_token_index = self._token_id[payment_token_label]
        requested_token_index = self._token_id[requested_token_label]

        self._token_amounts[payment_token_index] += payment_token_amount
        self._token_amounts[requested_token_index] -= returned_token_amount

        return returned_token_amount

    def get_D(self):
        # computes the D value in StableSwap formula
        return ut.curve_get_D(self._token_amounts, self._last_amplification)

    def get_price_slippage(self, payment_token_label, requested_token_label, payment_token_amount,
                           reverse_slippage=False):
        """
            Calculate price slippage, defined as the percent difference between the actual price of
            the executed exchange and the price just before the exchange.
            :param payment_token_label: payment token label
            :param requested_token_label: requested token label
            :param payment_token_amount: payment token amount
            :param reverse_slippage: compute slippage of 1/price
            :return:
        """

        returned_token_amount = self.get_requested_token_amount(payment_token_label, requested_token_label,
                                                                payment_token_amount, fee_ratio=self._fee_ratio)

        exchange_price = payment_token_amount / returned_token_amount
        price_before_exchange = self.get_price(payment_token_label, requested_token_label)

        if reverse_slippage:
            exchange_price = 1 / exchange_price
            price_before_exchange = 1 / price_before_exchange

            return (exchange_price - price_before_exchange) / price_before_exchange

        else:


            return (exchange_price - price_before_exchange) / price_before_exchange



