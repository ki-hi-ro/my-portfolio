from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import unquote, urlparse


DATA_DIR = Path(__file__).resolve().parent / "data"
START_YEAR = 2017

CATEGORY_LABELS = {
    "work": "制作物",
    "career": "職務経歴",
    "article": "技術ブログ",
    "learning": "学習記録",
    "other": "その他",
    "raw": "未整理",
}

CATEGORY_ORDER = ("learning", "article", "work", "career", "other", "raw")

SOURCE_LABELS = {
    "portfolio": "登録CSV",
    "euphoria": "ki-hi-ro.com",
    "github": "GitHub",
    "paiza": "paiza",
    "progate": "Progate",
    "xserver": "エックスサーバー",
    "crowdworks": "クラウドワークス",
    "career": "職務経歴",
}

PRIVATE_METADATA_KEYS = {
    "アクセス制限のログイン情報",
    "login",
    "password",
    "basic_auth",
    "auth",
    "secret",
    "token",
    "key",
}

INTERNAL_METADATA_KEYS = {
    "titleGeneratedFromUrl",
}


@dataclass(frozen=True)
class CsvReadResult:
    rows: list[dict[str, str]]
    exists: bool
    encoding: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class TimelineItem:
    id: str
    source_type: str
    source_file: str
    date: date | None = None
    period: str | None = None
    year: int | None = None
    category: str = "raw"
    title: str = "Untitled"
    summary: str = ""
    detail: str = ""
    source_url: str | None = None
    tags: tuple[str, ...] = ()
    is_published: bool = False
    needs_review: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def category_label(self) -> str:
        return CATEGORY_LABELS.get(self.category, self.category)

    @property
    def source_label(self) -> str:
        return SOURCE_LABELS.get(self.source_type, self.source_type)

    @property
    def primary_action_label(self) -> str:
        labels = {
            "github": "GitHubで見る",
            "paiza": "Paizaで見る",
            "portfolio": "公開URLを見る",
            "euphoria": "記事を見る",
            "xserver": "公開URLを見る",
            "crowdworks": "契約URLを見る",
        }

        return labels.get(self.source_type, "公開URLを見る")

    @property
    def period_label(self) -> str:
        if self.period:
            return self.period
        if self.date:
            return self.date.strftime("%Y.%m.%d")
        return "日付未設定"

    @property
    def current_label(self) -> str:
        if self.date:
            return f"{self.date.strftime('%Y.%m')} / {self.category_label}"
        if self.period:
            return f"{self.period} / {self.category_label}"
        return f"時期未設定 / {self.category_label}"

    @property
    def datetime_value(self) -> str:
        return self.date.isoformat() if self.date else ""

    @property
    def has_date(self) -> bool:
        return self.date is not None

    @property
    def has_year(self) -> bool:
        return self.year is not None

    @property
    def is_timeline_ready(self) -> bool:
        return self.has_date and self.is_published and not self.needs_review

    @property
    def is_public_candidate(self) -> bool:
        return self.is_published or _is_positive_flag(_clean(self.metadata.get("実績フラグ"))) or _is_positive_flag(_clean(self.metadata.get("実績")))

    @property
    def public_metadata_items(self) -> list[tuple[str, Any]]:
        items: list[tuple[str, Any]] = []

        for key, value in self.metadata.items():
            if value in (None, ""):
                continue

            if _is_private_metadata_key(key) or _is_private_metadata_value(value):
                continue

            items.append((key, value))

        return items

    @property
    def overview_text(self) -> str:
        if self.source_type == "paiza":
            rank = _clean(self.metadata.get("ランク"))
            language = _clean(self.metadata.get("言語"))
            result = _clean(self.metadata.get("結果"))
            score = _clean(self.metadata.get("スコア"))

            if rank or language or result or score:
                challenge = f"paizaランク{rank}の問題" if rank else "paizaの問題"
                language_text = f"{language}で" if language else ""
                result_text = _join_summary(score, result).replace(" / ", "で")

                if result_text:
                    return f"{challenge}に{language_text}挑戦した記録です。結果は{result_text}となりました。"

                return f"{challenge}に{language_text}挑戦した記録です。"

        return self.detail or self.summary

    @property
    def metadata_summary(self) -> str:
        parts: list[str] = []

        for key, value in self.public_metadata_items[:5]:
            text_value = _clean(value)

            if len(text_value) > 80:
                text_value = f"{text_value[:77]}..."

            parts.append(f"{key}: {text_value}")

        return " / ".join(parts) if parts else "-"

    @property
    def draft_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []

        if not self.has_date:
            reasons.append("date が未設定")
        if not self.has_year:
            reasons.append("year が未設定")
        if not self.is_published:
            reasons.append("isPublished が false")
        if self.needs_review:
            reasons.append("needsReview が true")
        if not _clean(self.title) or self.title in {"Untitled", "Euphoria URL", "GitHub Repository", "クラウドワークス案件", "職務経歴参照データ"}:
            reasons.append("title が空または仮設定")
        if not self.source_url:
            reasons.append("sourceUrl が空")
        if self.metadata.get("titleGeneratedFromUrl"):
            reasons.append("sourceUrl のみで title が仮生成")
        if self.metadata.get("categoryInferred"):
            reasons.append("category が推定")
        if self.is_public_candidate and (not self.has_date or self.needs_review):
            reasons.append("公開候補だが詳細未整理")

        return tuple(dict.fromkeys(reasons))

    @property
    def draft_reason_text(self) -> str:
        if self.is_timeline_ready:
            return "公開タイムライン対象"

        return " / ".join(self.draft_reasons) if self.draft_reasons else "公開条件未達"

    @property
    def publish_status(self) -> str:
        if self.is_published and not self.needs_review and self.date:
            return "公開中"
        if self.is_published and not self.date:
            return "公開候補 / 日付待ち"
        if self.needs_review:
            return "要確認"
        return "非公開"


@dataclass(frozen=True)
class TimelineDataset:
    all_items: tuple[TimelineItem, ...]
    published_items: tuple[TimelineItem, ...]
    timeline_items: tuple[TimelineItem, ...]
    draft_items: tuple[TimelineItem, ...]
    raw_items: tuple[TimelineItem, ...]
    years: tuple[int, ...]
    year_counts: dict[int, int]
    source_statuses: tuple[dict[str, Any], ...]
    summary_counts: dict[str, int]
    source_type_counts: dict[str, int]
    category_counts: dict[str, int]
    category_options: tuple[tuple[str, str, int], ...]
    draft_reason_counts: dict[str, int]
    current_year: int

    def items_for_year(self, year: int | None) -> tuple[TimelineItem, ...]:
        if year is None:
            return self.timeline_items

        return tuple(item for item in self.timeline_items if item.year == year)

    def items_for_filters(self, year: int | None, category: str | None) -> tuple[TimelineItem, ...]:
        items = self.items_for_year(year)

        if category is None:
            return items

        return tuple(item for item in items if item.category == category)

    def year_counts_for_category(self, category: str | None) -> dict[int, int]:
        if category is None:
            return self.year_counts

        return {
            year: sum(1 for item in self.timeline_items if item.year == year and item.category == category)
            for year in self.years
        }

    def find_public_item(self, item_id: str) -> TimelineItem | None:
        for item in self.timeline_items:
            if item.id == item_id:
                return item

        return None


def _clean(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _is_private_metadata_key(key: Any) -> bool:
    normalized_key = str(key).strip().lower()

    private_keys = {str(value).strip().lower() for value in PRIVATE_METADATA_KEYS}
    internal_keys = {str(value).strip().lower() for value in INTERNAL_METADATA_KEYS}

    private_patterns = (
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_key",
        "private_key",
        "basic_auth",
        "authorization",
        "auth",
        "login",
    )

    return (
        normalized_key in private_keys
        or normalized_key in internal_keys
        or any(pattern in normalized_key for pattern in private_patterns)
    )


def _is_private_metadata_value(value: Any) -> bool:
    normalized_value = _clean(value).lower()
    private_patterns = (
        "アクセス制限",
        "basic auth",
        "basic_auth",
        "authorization",
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_key",
        "private_key",
    )

    return any(pattern in normalized_value for pattern in private_patterns)



def _pick(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = _clean(row.get(key))

        if value:
            return value

    return ""


def _parse_date(value: str) -> date | None:
    value = _clean(value)

    if not value:
        return None

    normalized = (
        value.replace("年", "/")
        .replace("月", "/")
        .replace("日", "")
        .replace("-", "/")
        .replace(".", "/")
    )

    for fmt in ("%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue

    return None


def _parse_year_month(value: str) -> date | None:
    value = _clean(value)

    if not value:
        return None

    normalized = (
        value.replace("年", "/")
        .replace("月", "")
        .replace(".", "/")
        .replace("-", "/")
    )

    for fmt in ("%Y/%m", "%Y"):
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue

    return None


def _parse_period_value(value: str) -> date | None:
    return _parse_date(value) or _parse_year_month(value)


def _parse_timeline_period(value: str) -> tuple[date | None, str | None]:
    raw_value = _clean(value)

    if not raw_value:
        return None, None

    exact_date = _parse_date(raw_value)

    if exact_date:
        return exact_date, None

    range_parts = [
        part
        for part in re.split(r"\s+-\s+|〜|~|–|—|から|to", raw_value)
        if _clean(part)
    ]

    if len(range_parts) >= 2:
        start_date = _parse_period_value(range_parts[0])
        end_date = _parse_period_value(range_parts[-1])

        return end_date or start_date, raw_value

    rough_date = _parse_year_month(raw_value)

    if rough_date:
        return rough_date, raw_value

    return None, raw_value


def _normalize_header(header: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: dict[str, int] = {}

    for index, value in enumerate(header, start=1):
        key = _clean(value) or f"column_{index}"
        seen[key] = seen.get(key, 0) + 1

        if seen[key] > 1:
            key = f"{key}_{seen[key]}"

        normalized.append(key)

    return normalized


def _row_to_dict(header: list[str], row: list[str]) -> dict[str, str]:
    header = _normalize_header(header)
    values = [_clean(value) for value in row]
    result = {key: values[index] if index < len(values) else "" for index, key in enumerate(header)}

    for index, value in enumerate(values[len(header) :], start=len(header) + 1):
        result[f"extra_{index}"] = value

    return result


def _looks_like_header(row: list[str], markers: tuple[str, ...]) -> bool:
    if not markers:
        return True

    normalized_cells = {_clean(cell).lower() for cell in row if _clean(cell)}
    normalized_markers = {_clean(marker).lower() for marker in markers}

    return any(
        marker in cell or cell in marker
        for cell in normalized_cells
        for marker in normalized_markers
    )


def _read_csv_result(
    source_file: str,
    fallback_headers: list[str] | None = None,
    header_markers: Iterable[str] | None = None,
    header_predicate: Callable[[list[str]], bool] | None = None,
) -> CsvReadResult:
    path = DATA_DIR / source_file

    if not path.exists():
        return CsvReadResult(rows=[], exists=False)

    raw_text: str | None = None
    encoding_used: str | None = None

    for encoding in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            raw_text = path.read_text(encoding=encoding)
            encoding_used = encoding
            break
        except UnicodeDecodeError:
            continue

    if raw_text is None:
        return CsvReadResult(rows=[], exists=True, error="CSV encoding could not be decoded")

    raw_rows = [
        [_clean(cell) for cell in row]
        for row in csv.reader(raw_text.splitlines())
        if any(_clean(cell) for cell in row)
    ]

    if not raw_rows:
        return CsvReadResult(rows=[], exists=True, encoding=encoding_used)

    if header_predicate:
        for index, row in enumerate(raw_rows):
            if header_predicate(row):
                header = row
                return CsvReadResult(
                    rows=[_row_to_dict(header, data_row) for data_row in raw_rows[index + 1 :]],
                    exists=True,
                    encoding=encoding_used,
                )

        return CsvReadResult(
            rows=[],
            exists=True,
            encoding=encoding_used,
            error="Header row was not found",
        )

    first_row = raw_rows[0]
    markers = tuple(header_markers or ())
    has_header = _looks_like_header(first_row, markers)

    if fallback_headers and not has_header:
        header = fallback_headers
        data_rows = raw_rows
    else:
        header = first_row
        data_rows = raw_rows[1:]

    return CsvReadResult(
        rows=[_row_to_dict(header, data_row) for data_row in data_rows],
        exists=True,
        encoding=encoding_used,
    )


def _item_id(
    source_type: str,
    source_file: str,
    row_index: int,
    title: str,
    item_date: date | None,
    source_url: str = "",
) -> str:
    stamp = item_date.strftime("%Y%m%d") if item_date else "nodate"
    raw = f"{source_type}|{source_file}|{row_index}|{title}|{item_date}|{source_url}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]

    return f"{source_type}-{stamp}-{row_index:04d}-{digest}"


def _title_from_url(url: str) -> str:
    parsed = urlparse(url)
    slug = unquote(parsed.path.rstrip("/").split("/")[-1])

    if not slug:
        return parsed.netloc or "Untitled"

    title = re.sub(r"[-_]+", " ", slug).strip()

    return title or "Untitled"


def _infer_category(value: str) -> str:
    if "制作" in value or "実績" in value or "work" in value.lower():
        return "work"
    if "職務" in value or "経歴" in value or "career" in value.lower():
        return "career"
    if "技術" in value or "ブログ" in value or "article" in value.lower():
        return "article"
    if "学習" in value or "paiza" in value.lower() or "progate" in value.lower():
        return "learning"
    if "その他" in value or "other" in value.lower():
        return "other"

    return "raw"


def normalize_category_key(value: str | None) -> str | None:
    normalized = _clean(value)

    if not normalized:
        return None

    if normalized in CATEGORY_LABELS:
        return normalized

    for key, label in CATEGORY_LABELS.items():
        if normalized == label:
            return key

    return None


def _is_positive_flag(value: str) -> bool:
    normalized = _clean(value).lower()

    return normalized in {"1", "true", "yes", "y", "公開", "実績", "◯", "○", "〇", "あり"}


def _join_summary(*parts: str) -> str:
    return " / ".join(part for part in (_clean(part) for part in parts) if part)


def normalize_euphoria_rows(
    rows: list[dict[str, str]],
    source_file: str = "Euphoria.csv",
    source_type: str = "euphoria",
) -> list[TimelineItem]:
    items: list[TimelineItem] = []

    for index, row in enumerate(rows, start=1):
        category_text = _pick(row, "カテゴリー", "category", "カテゴリ")
        url = _pick(row, "公開URL", "URL", "url", "sourceUrl", "記事URL")
        period_text = _pick(row, "時期", "period", "期間")
        item_date, period = _parse_timeline_period(period_text)
        published_at = _pick(row, "投稿日", "published_at", "publishedAt", "date", "公開日")
        published_date = _parse_date(published_at)

        if published_date:
            item_date = published_date
            period = None

        category = _infer_category(category_text)
        title_text = _pick(row, "タイトル", "title", "件名", "name")
        title = title_text or (_title_from_url(url) if url else "公開記録")
        category_label = CATEGORY_LABELS.get(category, category_text or "公開記録")
        summary = _pick(row, "コメント", "comment", "概要", "summary", "説明") or f"{category_label}として公開した記録です。"
        detail = _pick(row, "詳細", "detail", "本文", "description") or summary
        is_registered_csv = source_type == "portfolio"
        is_published = item_date is not None and (bool(url) or is_registered_csv)
        needs_review = item_date is None or (not bool(url) and not is_registered_csv)

        items.append(
            TimelineItem(
                id=_item_id(source_type, source_file, index, title, item_date, url),
                source_type=source_type,
                source_file=source_file,
                date=item_date,
                period=period,
                year=item_date.year if item_date else None,
                category=category,
                title=title,
                summary=summary,
                detail=detail,
                source_url=url or None,
                tags=tuple(tag for tag in (category_label,) if tag),
                is_published=is_published,
                needs_review=needs_review,
                metadata={
                    "時期": period_text,
                    "カテゴリー": category_text,
                    "タイトル": title_text,
                    "コメント": summary,
                    "投稿日": item_date.strftime("%Y.%m.%d") if item_date else "",
                    "categoryInferred": not bool(category_text),
                    "titleGeneratedFromUrl": not bool(title_text) and bool(url),
                },
            )
        )

    return items


def normalize_portfolio_rows(rows: list[dict[str, str]], source_file: str = "data.csv") -> list[TimelineItem]:
    return normalize_euphoria_rows(rows, source_file, source_type="portfolio")


def normalize_github_rows(rows: list[dict[str, str]], source_file: str = "GitHub.csv") -> list[TimelineItem]:
    items: list[TimelineItem] = []

    for index, row in enumerate(rows, start=1):
        title = _pick(row, "name", "リポジトリ名", "repository", "Repository", "repo", "リポジトリ") or "GitHub Repository"
        url = _pick(row, "repositoryUrl", "URL", "url", "GitHub URL", "html_url")
        description = _pick(row, "description", "説明")
        visibility = _pick(row, "visibility", "公開状態", "public")
        achievement_flag = _pick(row, "achievementFlag", "実績フラグ", "実績", "achievement")
        is_candidate = _is_positive_flag(achievement_flag)

        items.append(
            TimelineItem(
                id=_item_id("github", source_file, index, title, None, url),
                source_type="github",
                source_file=source_file,
                category="work",
                title=title,
                summary=description or "GitHubリポジトリの制作物候補です。",
                source_url=url or None,
                is_published=is_candidate,
                needs_review=True,
                metadata={
                    "公開状態": visibility,
                    "実績フラグ": achievement_flag,
                },
            )
        )

    return items


def normalize_paiza_rows(rows: list[dict[str, str]], source_file: str = "paiza.csv") -> list[TimelineItem]:
    items: list[TimelineItem] = []

    for index, row in enumerate(rows, start=1):
        item_date = _parse_date(_pick(row, "提出日", "date", "日時"))
        title = _pick(row, "問題", "title") or "paiza 提出記録"
        rank = _pick(row, "ランク", "rank")
        language = _pick(row, "言語", "language")
        answer_time = _pick(row, "解答時間", "time")
        result = _pick(row, "結果", "result")
        score = _pick(row, "スコア", "score")
        url = _pick(row, "URL", "url")
        comment = _pick(row, "コメント", "comment", "summary", "メモ")
        result_text = _join_summary(score, result).replace(" / ", "で")
        summary = comment or (
            f"ランク{rank}の問題に{language}で挑戦。結果は{result_text}でした。"
            if rank and language and result_text
            else _join_summary(rank, language, result, score)
        )
        detail = _pick(row, "詳細", "detail") or _join_summary(
            "paizaの提出履歴をもとにした学習記録です。",
            f"解答時間: {answer_time}" if answer_time else "",
        )

        items.append(
            TimelineItem(
                id=_item_id("paiza", source_file, index, title, item_date, url),
                source_type="paiza",
                source_file=source_file,
                date=item_date,
                year=item_date.year if item_date else None,
                category="learning",
                title=title,
                summary=summary or "paizaの学習記録です。",
                detail=detail or "paizaの提出履歴です。",
                source_url=url or None,
                tags=tuple(tag for tag in (rank, language, result) if tag),
                is_published=item_date is not None,
                needs_review=item_date is None,
                metadata={
                    "ランク": rank,
                    "言語": language,
                    "解答時間": answer_time,
                    "結果": result,
                    "スコア": score,
                },
            )
        )

    return items


def normalize_progate_rows(rows: list[dict[str, str]], source_file: str = "Progate.csv") -> list[TimelineItem]:
    items: list[TimelineItem] = []

    for index, row in enumerate(rows, start=1):
        item_date = _parse_date(_pick(row, "支払日", "date", "決済日"))
        plan = _pick(row, "プラン", "plan", "Plan")
        period_start = _pick(row, "契約期間開始", "periodStart", "開始日")
        period_end = _pick(row, "契約期間終了", "periodEnd", "終了日")
        amount = _pick(row, "金額", "amount", "支払金額")
        period = _join_summary(period_start, period_end).replace(" / ", "〜")

        items.append(
            TimelineItem(
                id=_item_id("progate", source_file, index, "Progate プラス契約", item_date),
                source_type="progate",
                source_file=source_file,
                date=item_date,
                period=period or None,
                year=item_date.year if item_date else None,
                category="learning",
                title="Progate プラス契約",
                summary=_join_summary(plan, period) or "Progateの学習投資記録です。",
                detail="学習成果そのものではなく、学習投資として確認するデータです。",
                is_published=False,
                needs_review=True,
                metadata={
                    "プラン": plan,
                    "契約期間開始": period_start,
                    "契約期間終了": period_end,
                    "金額": amount,
                },
            )
        )

    return items


def normalize_xserver_rows(rows: list[dict[str, str]], source_file: str = "エックスサーバー.csv") -> list[TimelineItem]:
    items: list[TimelineItem] = []

    for index, row in enumerate(rows, start=1):
        first = _pick(row, "第一階層")
        second = _pick(row, "第二階層")
        third = _pick(row, "第三階層")
        url = _pick(row, "公開URL", "URL", "url")
        cms = _pick(row, "CMS")
        related_blog = _pick(row, "関連ブログ記事")
        achievement = _pick(row, "実績", "実績フラグ")
        title = " / ".join(part for part in (first, second, third) if part) or _title_from_url(url)
        is_candidate = _is_positive_flag(achievement)
        title_generated_from_url = not any((first, second, third)) and bool(url)

        items.append(
            TimelineItem(
                id=_item_id("xserver", source_file, index, title, None, url),
                source_type="xserver",
                source_file=source_file,
                category="work",
                title=title,
                summary=_join_summary(cms, related_blog, achievement) or "サーバー上の制作物候補です。",
                source_url=url or None,
                is_published=is_candidate,
                needs_review=True,
                metadata={
                    "第一階層": first,
                    "第二階層": second,
                    "第三階層": third,
                    "CMS": cms,
                    "関連ブログ記事": related_blog,
                    "実績": achievement,
                    "titleGeneratedFromUrl": title_generated_from_url,
                },
            )
        )

    return items


def normalize_crowdworks_rows(rows: list[dict[str, str]], source_file: str = "クラウドワークス.csv") -> list[TimelineItem]:
    items: list[TimelineItem] = []

    for index, row in enumerate(rows, start=1):
        client = _pick(row, "クライアント", "client", "発注者")
        title = _pick(row, "タイトル", "title", "案件名") or "クラウドワークス案件"
        url = _pick(row, "URL", "url", "契約URL")

        items.append(
            TimelineItem(
                id=_item_id("crowdworks", source_file, index, title, None, url),
                source_type="crowdworks",
                source_file=source_file,
                category="career",
                title=title,
                summary=client or "クラウドワークスの契約・案件候補です。",
                source_url=url or None,
                is_published=False,
                needs_review=True,
                metadata={
                    "クライアント": client,
                    "契約URL": url,
                },
            )
        )

    return items


def normalize_career_rows(rows: list[dict[str, str]], source_file: str = "職務経歴.csv") -> list[TimelineItem]:
    items: list[TimelineItem] = []

    for index, row in enumerate(rows, start=1):
        values = [value for value in row.values() if value]
        title = values[0] if values else "職務経歴参照データ"

        items.append(
            TimelineItem(
                id=_item_id("career", source_file, index, title, None),
                source_type="career",
                source_file=source_file,
                category="raw",
                title=title,
                summary="職務経歴データを補完する参照情報です。",
                is_published=False,
                needs_review=True,
                metadata={key: value for key, value in row.items() if value},
            )
        )

    return items


normalizePortfolioRows = normalize_portfolio_rows
normalizeEuphoriaRows = normalize_euphoria_rows
normalizeGitHubRows = normalize_github_rows
normalizePaizaRows = normalize_paiza_rows
normalizeProgateRows = normalize_progate_rows
normalizeXserverRows = normalize_xserver_rows
normalizeCrowdWorksRows = normalize_crowdworks_rows
normalizeCareerRows = normalize_career_rows


def load_timeline_dataset() -> TimelineDataset:
    current_year = date.today().year
    source_configs = (
        {
            "source_type": "portfolio",
            "source_file": "data.csv",
            "normalizer": normalize_portfolio_rows,
            "reader_options": {"header_markers": ("時期", "カテゴリー", "タイトル", "コメント", "公開URL")},
        },
        {
            "source_type": "euphoria",
            "source_file": "Euphoria.csv",
            "normalizer": normalize_euphoria_rows,
            "reader_options": {"header_markers": ("カテゴリー", "URL", "category", "url", "時期", "公開URL")},
        },
        {
            "source_type": "github",
            "source_file": "GitHub.csv",
            "normalizer": normalize_github_rows,
            "reader_options": {
                "fallback_headers": ["name", "repositoryUrl", "description", "visibility", "achievementFlag"],
                "header_markers": ("リポジトリ", "URL", "説明", "公開", "実績", "name", "repository"),
            },
        },
        {
            "source_type": "paiza",
            "source_file": "paiza.csv",
            "normalizer": normalize_paiza_rows,
            "reader_options": {"header_markers": ("提出日", "問題", "ランク")},
        },
        {
            "source_type": "progate",
            "source_file": "Progate.csv",
            "normalizer": normalize_progate_rows,
            "reader_options": {"header_predicate": lambda row: "支払日" in row and "プラン" in row},
        },
        {
            "source_type": "xserver",
            "source_file": "エックスサーバー.csv",
            "normalizer": normalize_xserver_rows,
            "reader_options": {"header_markers": ("第一階層", "公開URL", "CMS", "実績")},
        },
        {
            "source_type": "crowdworks",
            "source_file": "クラウドワークス.csv",
            "normalizer": normalize_crowdworks_rows,
            "reader_options": {"header_markers": ("クライアント", "タイトル", "URL")},
        },
        {
            "source_type": "career",
            "source_file": "職務経歴.csv",
            "normalizer": normalize_career_rows,
            "reader_options": {"header_markers": ("職務", "経歴", "URL", "サービス")},
        },
    )

    all_items: list[TimelineItem] = []
    source_statuses: list[dict[str, Any]] = []

    for config in source_configs:
        source_file = config["source_file"]
        csv_result = _read_csv_result(source_file, **config["reader_options"])
        rows = csv_result.rows
        items = config["normalizer"](rows, source_file)
        all_items.extend(items)
        source_statuses.append(
            {
                "source_type": config["source_type"],
                "source_label": SOURCE_LABELS[config["source_type"]],
                "source_file": source_file,
                "exists": csv_result.exists,
                "encoding": csv_result.encoding or "-",
                "error": csv_result.error or "",
                "rows": len(rows),
                "items": len(items),
                "timeline_ready": sum(1 for item in items if item.is_timeline_ready),
                "draft": sum(1 for item in items if not item.is_timeline_ready),
                "date_present": sum(1 for item in items if item.has_date),
                "date_missing": sum(1 for item in items if not item.has_date),
                "needs_review": sum(1 for item in items if item.needs_review),
                "public_candidates": sum(1 for item in items if item.is_public_candidate),
            }
        )

    published_items = tuple(
        item
        for item in all_items
        if item.is_published and not item.needs_review
    )
    timeline_items = tuple(
        sorted(
            (item for item in published_items if item.date is not None),
            key=lambda item: (item.date or date.min, item.title),
            reverse=True,
        )
    )
    draft_items = tuple(
        sorted(
            (item for item in all_items if item not in timeline_items),
            key=lambda item: (item.source_type, item.source_file, item.title),
        )
    )
    raw_items = tuple(item for item in all_items if item.category == "raw" or item.date is None)
    max_item_year = max((item.year or START_YEAR for item in all_items), default=START_YEAR)
    max_year = max(current_year, max_item_year)
    years = tuple(range(START_YEAR, max_year + 1))
    year_counts = {
        year: sum(1 for item in timeline_items if item.year == year)
        for year in years
    }
    source_type_counts = dict(Counter(item.source_type for item in all_items))
    category_counts = dict(Counter(item.category for item in timeline_items))
    category_options = tuple(
        (category, CATEGORY_LABELS.get(category, category), category_counts[category])
        for category in CATEGORY_ORDER
        if category_counts.get(category, 0) > 0
    )
    draft_reason_counts = dict(Counter(reason for item in draft_items for reason in item.draft_reasons))
    summary_counts = {
        "allItems": len(all_items),
        "publishedItems": len(published_items),
        "timelineItems": len(timeline_items),
        "draftItems": len(draft_items),
        "rawItems": len(raw_items),
        "datePresent": sum(1 for item in all_items if item.has_date),
        "dateMissing": sum(1 for item in all_items if not item.has_date),
        "needsReview": sum(1 for item in all_items if item.needs_review),
        "publicCandidates": sum(1 for item in all_items if item.is_public_candidate),
    }

    return TimelineDataset(
        all_items=tuple(all_items),
        published_items=published_items,
        timeline_items=timeline_items,
        draft_items=draft_items,
        raw_items=raw_items,
        years=years,
        year_counts=year_counts,
        source_statuses=tuple(source_statuses),
        summary_counts=summary_counts,
        source_type_counts=source_type_counts,
        category_counts=category_counts,
        category_options=category_options,
        draft_reason_counts=draft_reason_counts,
        current_year=current_year,
    )
