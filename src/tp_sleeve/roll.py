"""tp_sleeve / roll — dated UST 10Y future contract selection + quarterly roll.

cTrader lists quarterly, expiring contracts (UST10Y_H6/M6/U6/Z6 = Mar/Jun/Sep/Dec
2026), NOT a continuous series. This module deterministically GENERATES the
standard quarterly contract chain and picks the front contract for a given date,
rolling out `ROLL_BUFFER_DAYS` before the delivery month begins.

Pure / no broker calls. The roll itself is realized by the normal CLOSE-FIRST
reconcile (`carry_sleeve.executor.plan_reconcile`): when the held contract is no
longer the front, it is not in the target -> CLOSE; the new front -> OPEN.
"""

from __future__ import annotations

from datetime import date, timedelta

from tp_sleeve.config import (
    CODE_TO_MONTH,
    CONTRACT_DECADE_BASE,
    CONTRACT_PREFIX,
    QUARTERLY_MONTH_CODE,
    ROLL_BUFFER_DAYS,
)

__all__ = [
    "contract_symbol",
    "parse_contract",
    "delivery_first_day",
    "upcoming_quarterly",
    "select_front_contract",
    "needs_roll",
]


def contract_symbol(year: int, month: int, prefix: str = CONTRACT_PREFIX) -> str:
    """(2026, 3) -> 'UST10Y_H6' (single-digit year suffix, per broker scan)."""
    if month not in QUARTERLY_MONTH_CODE:
        raise ValueError(f"month {month} is not a quarterly delivery month (3/6/9/12)")
    return f"{prefix}_{QUARTERLY_MONTH_CODE[month]}{year % 10}"


def parse_contract(
    symbol: str,
    prefix: str = CONTRACT_PREFIX,
    decade_base: int = CONTRACT_DECADE_BASE,
) -> tuple[int, int]:
    """'UST10Y_H6' -> (2026, 3). Decodes the single-digit year against decade_base."""
    head = f"{prefix}_"
    if not symbol.startswith(head):
        raise ValueError(f"{symbol!r} does not start with {head!r}")
    suffix = symbol[len(head) :]
    if len(suffix) < 2:
        raise ValueError(f"bad contract suffix in {symbol!r}")
    code, year_digits = suffix[0], suffix[1:]
    if code not in CODE_TO_MONTH:
        raise ValueError(f"unknown month code {code!r} in {symbol!r}")
    if not year_digits.isdigit():
        raise ValueError(f"bad year digits {year_digits!r} in {symbol!r}")
    year = decade_base + int(year_digits) if len(year_digits) == 1 else int(year_digits)
    return year, CODE_TO_MONTH[code]


def delivery_first_day(year: int, month: int) -> date:
    """First calendar day of the contract's delivery month."""
    return date(year, month, 1)


def upcoming_quarterly(as_of: date, count: int = 8) -> list[tuple[int, int]]:
    """The next `count` quarterly (year, month) deliveries on/after `as_of`'s month."""
    if count < 1:
        raise ValueError("count must be >= 1")
    out: list[tuple[int, int]] = []
    y = as_of.year
    while len(out) < count:
        for mm in (3, 6, 9, 12):
            if (y, mm) >= (as_of.year, as_of.month):
                out.append((y, mm))
                if len(out) >= count:
                    break
        y += 1
    return out


def select_front_contract(
    as_of: date,
    prefix: str = CONTRACT_PREFIX,
    roll_buffer_days: int = ROLL_BUFFER_DAYS,
) -> str:
    """Front contract for `as_of`: earliest quarterly whose delivery month starts
    more than `roll_buffer_days` ahead (i.e. we have rolled out of any contract
    within the buffer of its delivery month)."""
    cutoff = as_of + timedelta(days=roll_buffer_days)
    for year, month in upcoming_quarterly(as_of, count=8):
        if delivery_first_day(year, month) > cutoff:
            return contract_symbol(year, month, prefix)
    raise ValueError("no front contract found (extend upcoming_quarterly count)")


def needs_roll(held_symbol: str | None, front_symbol: str) -> bool:
    """True if a non-empty held contract differs from the current front."""
    return bool(held_symbol) and held_symbol != front_symbol
