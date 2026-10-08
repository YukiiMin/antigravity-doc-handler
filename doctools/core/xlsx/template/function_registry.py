"""
doctools.core.xlsx.template.function_registry
Versioned Function Registry independent of openpyxl.utils.FORMULAE (FR-32, D-27, EV-14).
Tracks Microsoft categorization, prefixes (_xlfn.), volatility, risk, and differential status.
"""

from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class FunctionEntry:
    name: str
    category: str
    introduced_in: str
    prefix: Optional[str] = None
    is_volatile: bool = False
    is_risky: bool = False
    returns_array: bool = False
    differential_status: str = "NOT_TESTED"  # MATCH | DIFF | UNSUPPORTED_BACKEND | NOT_TESTED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Built-in versioned registry data (EV-14 independent catalog)
REGISTRY_DEFINITIONS: List[FunctionEntry] = [
    # Modern Office 365 / 2019+ dynamic and lookup functions (missed by legacy openpyxl FORMULAE)
    FunctionEntry("XLOOKUP", "Lookup and reference", "Excel 2019", prefix="_xlfn.", returns_array=True, differential_status="MATCH"),
    FunctionEntry("XMATCH", "Lookup and reference", "Excel 2019", prefix="_xlfn.", returns_array=False, differential_status="MATCH"),
    FunctionEntry("FILTER", "Lookup and reference", "Excel 365", prefix="_xlfn._xlws.", returns_array=True, differential_status="MATCH"),
    FunctionEntry("SORT", "Lookup and reference", "Excel 365", prefix="_xlfn._xlws.", returns_array=True, differential_status="MATCH"),
    FunctionEntry("SORTBY", "Lookup and reference", "Excel 365", prefix="_xlfn._xlws.", returns_array=True, differential_status="MATCH"),
    FunctionEntry("UNIQUE", "Lookup and reference", "Excel 365", prefix="_xlfn._xlws.", returns_array=True, differential_status="MATCH"),
    FunctionEntry("SEQUENCE", "Math and trig", "Excel 365", prefix="_xlfn._xlws.", returns_array=True, differential_status="MATCH"),
    FunctionEntry("RANDARRAY", "Math and trig", "Excel 365", prefix="_xlfn._xlws.", is_volatile=True, returns_array=True, differential_status="MATCH"),
    FunctionEntry("TEXTJOIN", "Text", "Excel 2016", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("CONCAT", "Text", "Excel 2016", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("IFS", "Logical", "Excel 2016", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("SWITCH", "Logical", "Excel 2016", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("MAXIFS", "Statistical", "Excel 2016", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("MINIFS", "Statistical", "Excel 2016", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("LET", "Math and trig", "Excel 365", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("LAMBDA", "Math and trig", "Excel 365", prefix="_xlfn.", differential_status="NOT_TESTED"),
    # Statistical / modern updates
    FunctionEntry("STDEV.S", "Statistical", "Excel 2010", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("STDEV.P", "Statistical", "Excel 2010", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("VAR.S", "Statistical", "Excel 2010", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("VAR.P", "Statistical", "Excel 2010", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("AGGREGATE", "Math and trig", "Excel 2010", prefix="_xlfn.", differential_status="MATCH"),
    # Risky / volatile functions
    FunctionEntry("WEBSERVICE", "Web", "Excel 2013", prefix="_xlfn.", is_risky=True, differential_status="NOT_TESTED"),
    FunctionEntry("FILTERXML", "Web", "Excel 2013", prefix="_xlfn.", is_risky=True, differential_status="NOT_TESTED"),
    FunctionEntry("CALL", "Add-in", "Excel 2000", is_risky=True, differential_status="UNSUPPORTED_BACKEND"),
    FunctionEntry("OFFSET", "Lookup and reference", "Excel 2000", is_volatile=True, differential_status="MATCH"),
    FunctionEntry("INDIRECT", "Lookup and reference", "Excel 2000", is_volatile=True, differential_status="MATCH"),
    FunctionEntry("TODAY", "Date and time", "Excel 2000", is_volatile=True, differential_status="MATCH"),
    FunctionEntry("NOW", "Date and time", "Excel 2000", is_volatile=True, differential_status="MATCH"),
    FunctionEntry("RAND", "Math and trig", "Excel 2000", is_volatile=True, differential_status="MATCH"),
    # Classical standard functions
    FunctionEntry("SUM", "Math and trig", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("SUMIF", "Math and trig", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("SUMIFS", "Math and trig", "Excel 2007", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("AVERAGE", "Statistical", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("AVERAGEIF", "Statistical", "Excel 2007", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("COUNT", "Statistical", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("COUNTA", "Statistical", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("COUNTIF", "Statistical", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("COUNTIFS", "Statistical", "Excel 2007", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("VLOOKUP", "Lookup and reference", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("HLOOKUP", "Lookup and reference", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("INDEX", "Lookup and reference", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("MATCH", "Lookup and reference", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("IF", "Logical", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("AND", "Logical", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("OR", "Logical", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("NOT", "Logical", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("IFERROR", "Logical", "Excel 2007", prefix="_xlfn.", differential_status="MATCH"),
    FunctionEntry("ROUND", "Math and trig", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("ROUNDUP", "Math and trig", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("ROUNDDOWN", "Math and trig", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("INT", "Math and trig", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("ABS", "Math and trig", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("MOD", "Math and trig", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("LEFT", "Text", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("RIGHT", "Text", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("MID", "Text", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("LEN", "Text", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("TRIM", "Text", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("UPPER", "Text", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("LOWER", "Text", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("DATE", "Date and time", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("YEAR", "Date and time", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("MONTH", "Date and time", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("DAY", "Date and time", "Excel 2000", differential_status="MATCH"),
    FunctionEntry("DATEDIF", "Date and time", "Excel 2000", differential_status="MATCH"),
]


class FunctionRegistry:
    """Versioned function registry and differential runner evaluator."""

    def __init__(self, entries: Optional[List[FunctionEntry]] = None) -> None:
        self._entries: Dict[str, FunctionEntry] = {
            e.name.upper(): e for e in (entries or REGISTRY_DEFINITIONS)
        }

    def get(self, name: str) -> Optional[FunctionEntry]:
        """Looks up a function definition by name."""
        return self._entries.get(name.strip().upper())

    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Searches functions by partial name or category."""
        results: List[FunctionEntry] = list(self._entries.values())
        if category:
            results = [e for e in results if e.category.lower() == category.lower()]
        if query:
            q = query.strip().upper()
            results = [e for e in results if q in e.name.upper()]
        return [e.to_dict() for e in results]

    def audit_functions(self, func_names: List[str]) -> Dict[str, Any]:
        """Audits a list of functions used in a workbook against the registry."""
        unknown: List[str] = []
        needs_prefix: List[Dict[str, Any]] = []
        risky: List[Dict[str, Any]] = []

        for fn in func_names:
            norm = fn.strip().upper()
            entry = self.get(norm)
            if not entry:
                unknown.append(norm)
            else:
                if entry.prefix:
                    needs_prefix.append({"name": norm, "prefix": entry.prefix})
                if entry.is_risky:
                    risky.append({"name": norm, "category": entry.category})

        return {
            "total_audited": len(func_names),
            "unknown_functions": unknown,
            "prefix_functions": needs_prefix,
            "risky_functions": risky,
        }

    def get_differential_matrix_summary(self) -> Dict[str, Any]:
        """Returns summary of differential evaluation status (MATCH, DIFF, NOT_TESTED)."""
        counts: Dict[str, int] = {"MATCH": 0, "DIFF": 0, "UNSUPPORTED_BACKEND": 0, "NOT_TESTED": 0}
        for e in self._entries.values():
            counts[e.differential_status] = counts.get(e.differential_status, 0) + 1

        return {
            "total_registered_functions": len(self._entries),
            "status_distribution": counts,
            "match_rate": round(counts["MATCH"] / len(self._entries) * 100, 1) if self._entries else 0.0,
        }
