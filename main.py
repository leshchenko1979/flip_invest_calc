import bisect

import pandas as pd
import streamlit as st

MIN_DOWNPAYMENT = 0.1

REPAIRS_SHARE = 0.2

LOAN_RATE = 0.14
TARGET_RATE = 0.2

MAX_RATES = {15: 0.4, 1_000_000_000: 0.6}

MAX_PRICE_FOR_FIXED_INCOME = 30

PROJECT_MANAGEMENT_FEE = 0.5


def main():
    st.set_page_config(
        page_title="Доходность инвестора во флиппинговых проектах с Алексеем Лещенко"
    )

    st.title("Сколько вы заработаете")
    st.caption(
        "Соинвестируя во [флиппинговые проекты с Алексеем Лещенко]"
        "(https://flipio.ru/invest.html)"
    )

    st.header("1. Введите суммы вложений")

    own, loan, purchase_price, duration = basic_inputs()

    st.divider()

    st.header("2. Выберите способ получения доходности:")

    fixed, ps = st.tabs(["Фиксированная доходность", "Разделение прибыли"])

    if purchase_price > MAX_PRICE_FOR_FIXED_INCOME:
        with fixed:
            st.warning("Для проектов такого размера доступно только разделение прибыли")
    else:
        with fixed:
            fixed_income(own, loan, purchase_price, duration)

    with ps:
        profit_share(own, loan, purchase_price, duration)


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
        min_value=10.0,
        max_value=100.0,
        step=0.1,
    )

    purchase_price = own + loan

    if own / purchase_price < MIN_DOWNPAYMENT:
        st.error("Доля первоначального взноса слишком мала.")
        st.stop()

    st.metric(
        "Cтоимость квартиры, млн. руб.",
        round(purchase_price, 2),
        help="Собственные средства + полученный ипотечный кредит",
    )

    duration = st.slider("Срок проекта, мес.", value=6, min_value=3, max_value=12)

    return own, loan, purchase_price, duration


def fixed_income(own, loan, purchase_price, duration):
    st.info(
        "Фиксированная процентная ставка, не зависящая от прибыли проекта. "
        "Ипотечные платежи оплачиваются за наш счёт."
    )

    # Расчёт own_share_income через WolframAlfa:
    # https://www.wolframalpha.com/input?i=%28x+*+a+%2B+r+*+b%29+%2F+%28a+%2B+b%29+%3D+t+what+is+x%3F

    thresholds = list(MAX_RATES.keys())
    rates = list(MAX_RATES.values())
    index = bisect.bisect(thresholds, int(purchase_price))
    max_rate = rates[index]

    own_income_rate = min(
        max_rate, loan * (TARGET_RATE - LOAN_RATE) / own + TARGET_RATE
    )

    assert (
        TARGET_RATE > (own * own_income_rate + loan * LOAN_RATE) / purchase_price - 0.01
    )

    st.divider()

    st.header("3. Результат:")

    st.metric(
        f"Ваша ставка доходности на вложенные средства ({own:.1f} млн. руб.)",
        f"{own_income_rate * 100:.0f}%",
    )

    own_income = own_income_rate * duration / 12 * own

    st.metric("Ваш доход за проект, млн. руб.", round(own_income, 2))


def profit_share(own, loan, purchase_price, duration):
    st.info(
        "Вы получаете долю от прибыли проекта. "
        "Ипотечные платежи оплачиваются вами, но включаются в расходы проекта."
    )

    repairs_approx = purchase_price * REPAIRS_SHARE

    repairs = st.slider(
        "Cтоимость ремонта, млн. руб.",
        value=repairs_approx,
        min_value=round(repairs_approx * 0.8, 1),
        max_value=round(repairs_approx * 1.2, 1),
        step=0.1,
    )

    total = purchase_price + repairs

    col1, col2, col3 = st.columns(3)

    col1.metric("Ваша инвестиция, млн. руб.", round(purchase_price, 2))
    col2.metric("Наша инвестиция, млн. руб.", round(repairs, 2))

    profit_share = purchase_price / total * (1 - PROJECT_MANAGEMENT_FEE)

    col3.metric(
        "Ваша доля от прибыли проекта",
        f"{100 * profit_share:.0f}%",
        help="Исходя из того, что 50% прибыли составляет вознаграждение за ведение проекта, "
        "а оставшая часть делится пропорционально сделанным вложениям инвестора и соинвестора",
    )

    sale_price = st.slider(
        "Стоимость продажи квартиры, млн. руб.",
        min_value=round(purchase_price + repairs),
        max_value=round(purchase_price * 2),
        value=round(purchase_price * 1.5),
        step=1,
    )

    taxes = (sale_price - purchase_price) * 0.13

    interest = LOAN_RATE * loan * duration / 12

    profit = sale_price - purchase_price - repairs - taxes - interest

    calc_table = pd.DataFrame(
        [
            ("Покупка", purchase_price),
            ("Ремонт", repairs),
            ("Проценты по кредиту", interest),
            ("Налоги (13%)", taxes),
            ("Продажа", sale_price),
            ("Прибыль", profit),
        ],
        columns=["Параметр", "Сумма, млн. руб."],
    ).set_index("Параметр")

    # calc_table["Сумма, млн. руб."] = [
    # round(float(x), 2) for x in calc_table["Сумма, млн. руб."]
    # ]

    st.caption("Расчет прибыли:")
    st.table(calc_table)

    st.divider()

    st.header("3. Результат:")

    own_income = profit * profit_share
    st.metric(
        "Ваш доход за проект, млн. руб.",
        round(own_income, 2),
        help="Прибыль проекта, умноженная на вашу долю",
    )

    own_income_rate = own_income / own / duration * 12

    st.metric(
        f"Ваша ставка доходности на вложенные средства ({own:.1f} млн. руб.)",
        f"{own_income_rate * 100:.0f}%",
    )


main()
