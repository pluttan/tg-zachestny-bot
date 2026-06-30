from utils.texts import t


def _v(value, default: str = "—") -> str:
    """Безопасное отображение значения: прочерк если None/пусто."""
    if value is None or value == "" or value == []:
        return default
    return str(value)


def format_fl_result(data: dict) -> str:
    lines = []
    lines.append(t("report_fl_title"))
    lines.append("\u2500" * 20)

    # Основные данные
    lines.append(f"\U0001f4cc <b>{_v(data.get('full_name'))}</b>")
    lines.append(f"    Дата рождения: {_v(data.get('birth_date'))}")
    lines.append("")

    # Документы
    lines.append(t("report_section_documents"))
    passport = data.get("passport", {})
    lines.append(f"    Паспорт: {_v(passport.get('status'))}")
    inn = data.get("inn", {})
    lines.append(f"    ИНН: {_v(inn.get('number'))} ({_v(inn.get('status'))})")
    lines.append(f"    Регион ИНН: {_v(inn.get('region'))}")
    dl = data.get("driver_license", {})
    lines.append(f"    Вод. удостоверение: {_v(dl.get('status'))}")
    lines.append("")

    # Нарушения
    lines.append(t("report_section_violations"))
    lines.append(f"    Розыск МВД: {_v(data.get('mvd_wanted'))}")
    lines.append(f"    ФСИН: {_v(data.get('fsin'))}")
    lines.append(f"    Реестр террористов: {_v(data.get('terrorist_list'))}")
    lines.append(f"    Реестр иноагентов: {_v(data.get('foreign_agent'))}")
    lines.append(f"    Дисквалификация: {_v(data.get('disqualified'))}")

    fines = data.get("gibdd_fines", {})
    if isinstance(fines, dict):
        lines.append(f"    Штрафы ГИБДД: {_v(fines.get('count', 0))} шт., {_v(fines.get('total_sum'))}")
    else:
        lines.append(f"    Штрафы ГИБДД: {_v(fines)}")
    lines.append("")

    # Финансы
    lines.append(t("report_section_debts"))
    bankruptcy = data.get("bankruptcy", {})
    if isinstance(bankruptcy, dict):
        lines.append(f"    Банкротство: {_v(bankruptcy.get('status'))}")
    else:
        lines.append(f"    Банкротство: {_v(bankruptcy)}")

    fssp = data.get("fssp", {})
    if isinstance(fssp, dict):
        lines.append(f"    Исп. производства ФССП: {_v(fssp.get('count', 0))} шт.")
    else:
        lines.append(f"    Исп. производства ФССП: {_v(fssp)}")

    tax = data.get("tax_debts", {})
    if isinstance(tax, dict):
        lines.append(f"    Налоговые долги: {_v(tax.get('status'))}")
    else:
        lines.append(f"    Налоговые долги: {_v(tax)}")

    lines.append(f"    Обеспечительные меры: {_v(data.get('security_measures'))}")
    lines.append(f"    Массовый руководитель: {_v(data.get('mass_head'))}")
    lines.append(f"    Кредитный индекс: {_v(data.get('credit_index'))}")
    lines.append("")

    # Суды
    lines.append(t("report_section_courts"))
    courts = data.get("courts_general", {})
    if isinstance(courts, dict):
        lines.append(f"    Общей юрисдикции: {_v(courts.get('total', 0))} дел")
        if courts.get("criminal"):
            lines.append(f"      \u2022 Уголовные: {courts['criminal']}")
        if courts.get("administrative"):
            lines.append(f"      \u2022 Административные: {courts['administrative']}")
        if courts.get("civil"):
            lines.append(f"      \u2022 Гражданские: {courts['civil']}")

    arb = data.get("arbitration", {})
    if isinstance(arb, dict):
        lines.append(f"    Арбитражные: {_v(arb.get('total', 0))} дел")
    lines.append("")

    # Предпринимательство
    lines.append(t("report_section_business"))
    egrip = data.get("egrul_egrip", [])
    if egrip:
        for entry in egrip:
            lines.append(f"    {_v(entry.get('type'))}: ОГРНИП {_v(entry.get('ogrnip'))}")
            lines.append(f"      Статус: {_v(entry.get('status'))}")
            lines.append(f"      Регион: {_v(entry.get('region'))}")
    else:
        lines.append("    ЕГРИП/ЕГРЮЛ: не найдено")

    roles = data.get("business_roles", [])
    if roles:
        lines.append("")
        lines.append("    <b>Должности:</b>")
        for role in roles:
            lines.append(f"      \u2022 {_v(role.get('company'))} \u2014 {_v(role.get('role'))}")
            lines.append(f"        Статус: {_v(role.get('status'))}")

    connections = data.get("business_connections", [])
    if connections:
        lines.append("")
        lines.append("    <b>Деловые связи:</b>")
        for conn in connections:
            lines.append(f"      \u2022 {conn}")
    lines.append("")

    # Дополнительно
    lines.append(t("report_section_extra"))
    lines.append(f"    Самозанятый: {_v(data.get('self_employed'))}")
    lines.append(f"    Реестр МСП: {_v(data.get('msp_registry'))}")

    contracts = data.get("gov_contracts", {})
    if isinstance(contracts, dict):
        lines.append(f"    Госзакупки: {_v(contracts.get('count', 0))} контрактов")
    lines.append(f"    Недобросовестный поставщик: {_v(data.get('unfair_supplier'))}")
    lines.append("")
    lines.append("\u2500" * 20)
    lines.append(t("report_footer"))

    return "\n".join(lines)


def format_ul_result(data: dict) -> str:
    lines = []
    lines.append(t("report_ul_title"))
    lines.append("\u2500" * 20)

    lines.append(f"\U0001f4cc <b>{_v(data.get('name'))}</b>")
    lines.append(f"    ИНН: {_v(data.get('inn'))}  |  ОГРН: {_v(data.get('ogrn'))}")
    lines.append(f"    Статус: {_v(data.get('status'))}")
    lines.append(f"    Дата регистрации: {_v(data.get('registration_date'))}")
    lines.append("")

    lines.append(t("report_section_management"))
    lines.append(f"    {_v(data.get('head_position'))}: {_v(data.get('head'))}")

    founders = data.get("founders", [])
    if founders:
        lines.append("    <b>Учредители:</b>")
        for f in founders:
            lines.append(f"      \u2022 {_v(f.get('name'))} \u2014 {_v(f.get('share'))}")
    lines.append("")

    lines.append(t("report_section_details"))
    lines.append(f"    Адрес: {_v(data.get('legal_address'))}")
    lines.append(f"    Уставный капитал: {_v(data.get('authorized_capital'))}")
    lines.append(f"    Сотрудников: {_v(data.get('employees_count'))}")
    lines.append(f"    Налогообложение: {_v(data.get('tax_system'))}")
    lines.append("")

    lines.append(t("report_section_activity"))
    lines.append(f"    Основной ОКВЭД: {_v(data.get('main_activity'))}")
    additional = data.get("additional_activities", [])
    if additional:
        lines.append("    Дополнительные:")
        for act in additional:
            lines.append(f"      \u2022 {act}")
    lines.append("")

    lines.append(t("report_section_risks"))
    lines.append(f"    Уровень риска ЦБ: {_v(data.get('cb_risk_level'))}")
    lines.append(f"    Налоговые риски: {_v(data.get('tax_risks'))}")
    lines.append(f"    Риск банкротства: {_v(data.get('bankruptcy_risk'))}")
    lines.append(f"    Стоп-лист банков: {_v(data.get('bank_stop_list'))}")
    lines.append(f"    Налоговые долги: {_v(data.get('fns_debts'))}")
    lines.append(f"    Реестр МСП: {_v(data.get('msp_registry'))}")
    lines.append(f"    Недобросовестный поставщик: {_v(data.get('unfair_supplier'))}")
    lines.append("")

    courts = data.get("courts", {})
    if isinstance(courts, dict) and courts.get("total", 0) > 0:
        lines.append(t("report_section_courts"))
        lines.append(f"    Всего дел: {courts['total']}")
        lines.append(f"    Истец: {_v(courts.get('as_plaintiff'))}")
        lines.append(f"    Ответчик: {_v(courts.get('as_defendant'))}")
        lines.append(f"    Общая сумма: {_v(courts.get('total_sum'))}")
        lines.append("")

    contracts = data.get("gov_contracts", {})
    if isinstance(contracts, dict):
        lines.append(t("report_section_contracts"))
        lines.append(f"    Контрактов: {_v(contracts.get('count'))}")
        lines.append(f"    На сумму: {_v(contracts.get('total_sum'))}")

    lines.append("")
    lines.append("\u2500" * 20)
    lines.append(t("report_footer"))

    return "\n".join(lines)


def format_ip_result(data: dict) -> str:
    lines = []
    lines.append(t("report_ip_title"))
    lines.append("\u2500" * 20)

    lines.append(f"\U0001f4cc <b>{_v(data.get('full_name'))}</b>")
    lines.append(f"    ОГРНИП: {_v(data.get('ogrnip'))}  |  ИНН: {_v(data.get('inn'))}")
    lines.append(f"    Статус: {_v(data.get('status'))}")
    lines.append(f"    Дата регистрации: {_v(data.get('registration_date'))}")
    term = data.get("termination_date")
    if term:
        lines.append(f"    Дата прекращения: {term}")
    lines.append(f"    Регион: {_v(data.get('region'))}")
    lines.append("")

    lines.append(t("report_section_activity"))
    lines.append(f"    Основной ОКВЭД: {_v(data.get('main_activity'))}")
    additional = data.get("additional_activities", [])
    if additional:
        lines.append("    Дополнительные:")
        for act in additional:
            lines.append(f"      \u2022 {act}")
    lines.append(f"    Налогообложение: {_v(data.get('tax_system'))}")
    lines.append(f"    Реестр МСП: {_v(data.get('msp_registry'))}")
    lines.append(f"    Самозанятый: {_v(data.get('self_employed'))}")
    lines.append("")

    lines.append(t("report_section_finance"))
    fssp = data.get("fssp", {})
    if isinstance(fssp, dict):
        lines.append(f"    Исп. производства ФССП: {_v(fssp.get('count', 0))} шт.")
    lines.append(f"    Налоговые долги: {_v(data.get('tax_debts'))}")
    lines.append(f"    Банкротство: {_v(data.get('bankruptcy'))}")
    lines.append(f"    Недобросовестный поставщик: {_v(data.get('unfair_supplier'))}")
    lines.append("")

    courts = data.get("courts", {})
    if isinstance(courts, dict) and courts.get("total", 0) > 0:
        lines.append(t("report_section_courts"))
        lines.append(f"    Всего дел: {courts['total']}")
        lines.append(f"    Истец: {_v(courts.get('as_plaintiff'))}")
        lines.append(f"    Ответчик: {_v(courts.get('as_defendant'))}")
        cases = courts.get("cases", [])
        for case in cases:
            lines.append(f"      \u2022 Дело {_v(case.get('number'))}: {_v(case.get('status'))}, {_v(case.get('sum'))}")
        lines.append("")

    contracts = data.get("gov_contracts", {})
    if isinstance(contracts, dict):
        lines.append(t("report_section_contracts"))
        lines.append(f"    Контрактов: {_v(contracts.get('count'))}")
        lines.append(f"    На сумму: {_v(contracts.get('total_sum'))}")

    lines.append("")
    lines.append("\u2500" * 20)
    lines.append(t("report_footer"))

    return "\n".join(lines)



def format_stats(stats: dict) -> str:
    period_names = {
        "day": t("stats_period_day"),
        "week": t("stats_period_week"),
        "month": t("stats_period_month"),
    }
    period_name = period_names.get(stats["period"], stats["period"])
    return t("stats_template",
        period=period_name,
        total_users=stats["total_users"],
        new_users=stats["new_users"],
        checks_count=stats["checks_count"],
        payments_sum=f"{stats['payments_sum']:.0f}",
    )


def format_prices(config) -> str:
    return t("prices",
        price_fl=f"{config.CHECK_PRICE_FL:.0f}",
        price_ul=f"{config.CHECK_PRICE_UL:.0f}",
        price_ip=f"{config.CHECK_PRICE_IP:.0f}",
    )
