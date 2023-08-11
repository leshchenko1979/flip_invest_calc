import streamlit as st
import pandas as pd

st.set_page_config()

st.header("Сколько вы заработаете")
st.caption("Соинвестируя во флиппинговые проекты с Алексеем Лещенко")

st.subheader("1. Введите суммы вложений")

col1, col2 = st.columns(2)
own = col1.number_input(
    "Вы вложите собственных средств, млн. руб.", value=1.0, min_value=1.0, step=0.1
)

loan = col2.number_input(
    "Вы возьмёте ипотечный кредит, млн. руб.", value=1.0, min_value=1.0, step=0.1
)

purchase_price = own + loan

repairs = purchase_price / 5

total = purchase_price + repairs

col1, col2, col3 = st.columns(3)
col1.metric("Cтоимость квартиры, млн. руб.", round(purchase_price, 2))
col2.metric(
    "Cтоимость ремонта, млн. руб.",
    round(repairs, 2),
)
col3.metric("Итого инвестиций, млн. руб.", round(total, 2))


duration = st.slider("Срок проекта, мес.", value=6, min_value=3, max_value=12)

st.subheader("2. Выберите способ получения доходности:")

fixed, ps = st.tabs(["Фиксированная доходность", "Разделение прибыли"])

with fixed:
    st.info(
        "Фиксированная процентная ставка, не зависящая от прибыли проекта. Ипотечные платежи оплачиваются за наш счёт."
    )

    # st.warning("Ипотечные платежи оплачиваются за ВАШ счёт!")

    own_share = own / purchase_price

    # Рассчёт own_share_income через WolframAlfa:
    # https://www.wolframalpha.com/input?i=%28x+*+a+%2B+r+*+b%29+%2F+%28a+%2B+b%29+%3D+t+what+is+x%3F

    TARGET_RATE = 0.2
    LOAN_RATE = 0.14

    own_income_rate = loan * (TARGET_RATE - LOAN_RATE) / own + TARGET_RATE

    assert (
        TARGET_RATE / (own * own_income_rate + loan * LOAN_RATE) / purchase_price < 0.01
    )

    st.subheader("3. Результат:")

    st.metric(
        f"Ваша ставка доходности на вложенные средства ({own:.1f} млн. руб.)",
        f"{own_income_rate * 100:.0f}%",
    )

    own_income = own_income_rate * duration / 12 * own

    st.metric("Ваш доход за проект, млн. руб.", round(own_income, 2))

with ps:
    st.info(
        "Вы получаете долю от прибыли проекта. "
        "Ипотечные платежи оплачиваются вами, но включаются в расходы проекта."
    )

    profit_share = purchase_price / (purchase_price + repairs) * 0.5

    st.metric(
        "Ваша доля от прибыли проекта",
        f"{100 * profit_share:.0f}%",
    )

    sale_price = st.slider(
        "Стоимость продажи квартиры, млн. руб.",
        min_value=round(purchase_price+repairs),
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

    calc_table["Сумма, млн. руб."] = [round(float(x), 2) for x in calc_table["Сумма, млн. руб."]]

    st.caption("Расчет прибыли:")
    st.table(calc_table)

    st.subheader("3. Результат:")

    own_income = profit * profit_share
    st.metric("Ваш доход за проект, млн. руб.", round(own_income, 2))

    own_income_rate = own_income / own / duration * 12

    st.metric(
        f"Ваша ставка доходности на вложенные средства ({own:.1f} млн. руб.)",
        f"{own_income_rate * 100:.0f}%",
    )
