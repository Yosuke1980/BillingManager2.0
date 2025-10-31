"""発注管理データモデル

発注管理機能で使用するデータモデルを定義します。
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Partner:
    """統合取引先マスター（Phase 6）"""
    id: Optional[int] = None
    name: str = ""
    code: str = ""
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    partner_type: str = "両方"  # 発注先/支払先/両方
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Supplier:
    """発注先マスター（将来的にPartnerに統合予定）"""
    id: Optional[int] = None
    name: str = ""
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Project:
    """案件マスター"""
    id: Optional[int] = None
    name: str = ""
    date: str = ""  # YYYY-MM-DD形式（単発案件の実施日）
    type: str = "単発"  # レギュラー/単発
    budget: float = 0.0
    parent_id: Optional[int] = None
    start_date: str = ""  # レギュラー案件の開始日
    end_date: str = ""  # レギュラー案件の終了日
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ExpenseOrder:
    """費用項目（発注管理用）"""
    id: Optional[int] = None
    project_id: int = 0
    item_name: str = ""
    amount: float = 0.0
    supplier_id: Optional[int] = None
    contact_person: str = ""
    status: str = "発注予定"
    order_number: str = ""
    order_date: str = ""
    implementation_date: str = ""
    invoice_received_date: str = ""
    payment_scheduled_date: str = ""
    payment_date: str = ""
    gmail_draft_id: str = ""
    gmail_message_id: str = ""
    email_sent_at: Optional[datetime] = None
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class OrderHistory:
    """発注履歴"""
    id: Optional[int] = None
    expense_id: int = 0
    order_number: str = ""
    email_subject: str = ""
    email_body: str = ""
    sent_to: str = ""
    gmail_draft_id: str = ""
    gmail_message_id: str = ""
    sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class StatusHistory:
    """ステータス履歴"""
    id: Optional[int] = None
    expense_id: int = 0
    old_status: str = ""
    new_status: str = ""
    changed_at: Optional[datetime] = None
    notes: str = ""


# ステータス定義
STATUS_ORDER_PLANNED = "発注予定"
STATUS_DRAFT_CREATED = "下書き作成済"
STATUS_ORDERED = "発注済"
STATUS_IMPLEMENTED = "実施済"
STATUS_INVOICE_WAITING = "請求書待ち"
STATUS_INVOICE_RECEIVED = "請求書受領"
STATUS_PAID = "支払済"

# ステータスリスト（順序保証）
STATUS_LIST = [
    STATUS_ORDER_PLANNED,
    STATUS_DRAFT_CREATED,
    STATUS_ORDERED,
    STATUS_IMPLEMENTED,
    STATUS_INVOICE_WAITING,
    STATUS_INVOICE_RECEIVED,
    STATUS_PAID,
]

# 案件タイプ
PROJECT_TYPE_REGULAR = "レギュラー"
PROJECT_TYPE_SINGLE = "単発"

PROJECT_TYPES = [PROJECT_TYPE_REGULAR, PROJECT_TYPE_SINGLE]

# 取引先区分（Phase 6）
PARTNER_TYPE_SUPPLIER = "発注先"
PARTNER_TYPE_PAYEE = "支払先"
PARTNER_TYPE_BOTH = "両方"

PARTNER_TYPES = [PARTNER_TYPE_SUPPLIER, PARTNER_TYPE_PAYEE, PARTNER_TYPE_BOTH]
