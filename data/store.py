# data/store.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

# 定义联系人对象
@dataclass
class Contact:
    id: str
    name: str
    ip: str
    port: int

# 定义消息对象
@dataclass
class Message:
    type: str  # "self", "peer", "system"
    content: str
    time: str
    sender_name: str = ""

class DataStore:
    def __init__(self):
        # 内存数据库
        self.contacts: List[Contact] = []
        self._history: Dict[str, List[Message]] = {} # key: ip

    def load_contacts(self, contacts_data: List[dict]):
        """将字典列表转换为 Contact 对象列表"""
        self.contacts = []
        for data in contacts_data:
            c = Contact(id=data.get("id", ""), name=data.get("name", "Unknown"), ip=data.get("ip", "0.0.0.0"), port=data.get("port", 9999))
            self.contacts.append(c)

    def get_contact_by_ip(self, ip: str) -> Optional[Contact]:
        for c in self.contacts:
            if c.ip == ip:
                return c
        return None

    def add_message(self, ip: str, content: str, msg_type: str, sender_name: str = "") -> Message:
        """存入一条消息并返回消息对象"""
        if ip not in self._history:
            self._history[ip] = []

        # 自动补全名字
        if not sender_name:
            if msg_type == "self":
                sender_name = "我"
            else:
                contact = self.get_contact_by_ip(ip)
                sender_name = contact.name if contact else ip

        msg = Message(
            type=msg_type,
            content=content,
            time=datetime.now().strftime("%H:%M"),
            sender_name=sender_name
        )
        self._history[ip].append(msg)
        return msg

    def get_history(self, ip: str) -> List[Message]:
        return self._history.get(ip, [])
