import bisect

import pandas as pd
import streamlit as st

MIN_DOWNPAYMENT = 0.1

REPAIRS_SHARE = 0.2

LOAN_RATE = 0.14
TARGET_RATE = 0.2

MAX_RATES = {1_000_000_000: 0.4}
THRESHOLDS = list(MAX_RATES.keys())
RATES = list(MAX_RATES.values())

MAX_PRICE_FOR_FIXED_INCOME = 40
MIN_PRICE_FOR_PROFIT_SHARE = 20

PROJECT_MANAGEMENT_FEE = 0.6


def main():
    st.set_page_config(
        page_title="Доходность инвестора во флиппинговых проектах с Алексеем Лещенко"
    )

    st.title("Сколько вы заработаете")
    st.caption(
        "Соинвестируя во [флиппинговые проекты с Алексеем Лещенко]"
        "(https://flipio.ru/invest.html)"
    )

    st.header("1. Введите суммы вложений и срок проекта")

    own, loan, purchase_price, duration = basic_inputs()

    st.divider()

    st.header("2. Выберите способ получения доходности:")

    fixed, ps = st.tabs(["Фиксированная доходность", "Разделение прибыли"])

    if purchase_price > MAX_PRICE_FOR_FIXED_INCOME:
        fixed.warning(
            "Фиксированная доходность недоступна для проектов, "
            "где стоимость покупки квартиры "
            f"более {MAX_PRICE_FOR_FIXED_INCOME} млн. руб."
        )
    else:
        with fixed:
            fixed_income(own, loan, purchase_price, duration)

    if purchase_price < MIN_PRICE_FOR_PROFIT_SHARE:
        ps.warning(
            "Раздел прибыли недоступен для проектов, "
            "где стоимость покупки квартиры "
            f"менее {MIN_PRICE_FOR_PROFIT_SHARE} млн. руб."
        )
    else:
        with ps:
            profit_share(own, loan, purchase_price, duration)

    st.divider()
    st.subheader("Заинтересовались? [Напишите нам](https://t.me/flippinginvestbot)!")


def basic_inputs():
    col1, col2 = st.columns(2)
    own = col1.number_input(
        "Вы вложите собственных средств, млн. руб.",
        value=2.0,
        min_value=1.0,
        max_value=100.0,
        step=0.1,
    )

    loan = col2.number_input(
        "Вы возьмёте ипотечный кредит, млн. руб.",
        value=10.0,
        min_value=0.0,
        max_value=100.0,
        step=0.1,
    )

    purchase_price = own + loan
    downpayment = own / purchase_price

    col1, col2 = st.columns(2)

    col1.metric(
        "Первоначальный взнос",
        f"{100 * downpayment:.0f}%" if loan > 0 else "Без ипотеки",
        help="Собственные средства / Стоимость квартиры",
    )

    col2.metric(
        "Cтоимость квартиры, млн. руб.",
        round(purchase_price, 2),
        help="Собственные средства + полученный ипотечный кредит",
    )

    if downpayment < MIN_DOWNPAYMENT:
        st.error(
            "Доля первоначального взноса дожна быть больше "
            f"{100 * MIN_DOWNPAYMENT:.0f}% (сейчас {100 * downpayment:.1f}%)."
        )
        st.stop()

    duration = st.slider("Срок проекта, мес.", value=5, min_value=3, max_value=8)

    return own, loan, purchase_price, duration


def fixed_income(own, loan, purchase_price, duration):
    st.info(
        """
        - Фиксированная процентная ставка, не зависящая от прибыли проекта.
        - Ипотечные платежи оплачиваются за наш счёт.
        - Ремонт оплачивается нами за наш счёт.
        - Расходы на налоги выдаются вам при окончательном расчёте."""
    )

    own_income_rate, own_income = calc_fixed_income(purchase_price, loan, own, duration)

    st.divider()

    st.header("3. Ваша доходность:")

    st.metric(
        f"Ставка на вложенные средства ({own:.1f} млн. руб.)",
        f"{own_income_rate * 100:.0f}% годовых",
        help="Зависит от размера первоначального платежа",
    )

    st.metric(
        "Доход за проект",
        f"{1_000_000 * round(own_income, 2):,.0f} руб.",
        help="Собственные средства * Ставка доходности * Срок проекта",
    )


def calc_fixed_income(purchase_price, loan, own, duration):
    # Расчёт own_income_rate через WolframAlfa:
    # https://www.wolframalpha.com/input?i=%28x+*+a+%2B+r+*+b%29+%2F+%28a+%2B+b%29+%3D+t+what+is+x%3F

    index = bisect.bisect(THRESHOLDS, int(purchase_price))
    max_rate = RATES[index]

    own_income_rate = min(
        max_rate, loan * (TARGET_RATE - LOAN_RATE) / own + TARGET_RATE
    )

    total_rate = (own * own_income_rate + loan * LOAN_RATE) / purchase_price

    assert TARGET_RATE > total_rate - 0.01

    own_income = own_income_rate * duration / 12 * own

    return own_income_rate, own_income


def profit_share(own, loan, purchase_price, duration):
    st.info(
        """
        - Вы получаете долю от прибыли проекта.
        - Ипотечные платежи оплачиваются вами за ваш счёт.
        - Ремонт оплачивается нами и включается в расходы проекта.
        - Расходы на налоги выдаются вам при окончательном расчёте."""
    )

    repairs = purchase_price * REPAIRS_SHARE

    profit_share = 1 - PROJECT_MANAGEMENT_FEE

    st.metric(
        "Ваша доля от прибыли проекта",
        f"{100 * profit_share:.0f}%",
    )

    sale_price = st.slider(
        "Стоимость продажи квартиры, млн. руб.",
        min_value=round(purchase_price + repairs),
        max_value=round(purchase_price * 2),
        value=round(purchase_price * 1.5),
        step=1,
    )

    taxes = (sale_price - purchase_price) * 0.13

    profit = sale_price - purchase_price - repairs - taxes

    st.divider()

    st.header("3. Ваша доходность:")

    interest = LOAN_RATE * loan * duration / 12

    own_income = profit * profit_share - interest

    st.metric(
        "Чистый доход за проект за вычетом процентов",
        f"{1_000_000 * round(own_income, 2):,.0f} руб.",
        help="Прибыль проекта, умноженная на вашу долю, за вычетом процентов по кредиту",
    )

    calc_table = pd.DataFrame(
        [
            ("Покупка", purchase_price),
            ("Ремонт", repairs),
            ("Налоги (13%)", taxes),
            ("Продажа", sale_price),
            ("Прибыль", profit),
        ],
        columns=["Параметр", "Сумма, млн. руб."],
    ).set_index("Параметр")

    with st.expander("Посмотреть расчёт прибыли проекта"):
        st.table(calc_table)

    calc_table = pd.DataFrame(
        [
            ("Прибыль проекта", profit),
            ("Ваша доля от прибыли проекта", profit * profit_share),
            ("Проценты по кредиту", interest),
            ("Чистый доход", own_income),
        ],
        columns=["Параметр", "Сумма, млн. руб."],
    ).set_index("Параметр")

    with st.expander("Посмотреть расчёт вашего чистого дохода"):
        st.table(calc_table)

    own_income_rate = own_income / own / duration * 12

    st.metric(
        f"Ставка на вложенные средства ({own:.1f} млн. руб.)",
        f"{own_income_rate * 100:.0f}% годовых",
        help="Доход / Собственные средства / Срок проекта",
    )


main()
