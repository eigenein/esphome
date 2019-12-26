#!/usr/bin/env python3
# coding: utf-8

"""
See also:
- https://github.com/esphome/esphome-core/blob/dev/src/esphome/api/api.proto
- https://github.com/esphome/esphome-core/blob/dev/src/esphome/api/api_message.h
"""

import socket
from binascii import hexlify
from dataclasses import dataclass
from time import sleep
from typing import Optional, Type, Iterable, ClassVar, List

from pure_protobuf.dataclasses_ import Message, field, message
from pure_protobuf.serializers import PackingSerializer, unsigned_varint_serializer
from pure_protobuf.types import int32, fixed32


PREAMBLE = b'\x00'


@dataclass
class BaseMessage:
    type_: ClassVar[int]


@message
@dataclass
class HelloRequest(BaseMessage):
    type_: ClassVar[int] = 1

    client_info: str = field(1, default='')


@message
@dataclass
class HelloResponse(BaseMessage):
    type_: ClassVar[int] = 2

    api_version_major: int32 = field(1, default=int32(0))
    api_version_minor: int32 = field(2, default=int32(0))
    server_info: str = field(3, default='')


@message
@dataclass
class ConnectRequest(BaseMessage):
    type_: ClassVar[int] = 3

    password: str = field(1, default='')


@message
@dataclass
class ConnectResponse(BaseMessage):
    type_: ClassVar[int] = 4

    invalid_password: bool = field(1, default=False)


@message
@dataclass
class LightCommandRequest(BaseMessage):
    type_: ClassVar[int] = 32

    key: fixed32 = field(1, default=fixed32(0))
    has_state: bool = field(2, default=False)
    state: bool = field(3, default=False)
    has_brightness: bool = field(4, default=False)
    brightness: float = field(5, default=0.0)
    has_rgb: bool = field(6, default=False)
    red: float = field(7, default=0.0)
    green: float = field(8, default=0.0)
    blue: float = field(9, default=0.0)
    has_white: bool = field(10, default=False)
    white: float = field(11, default=0.0)
    has_color_temperature: bool = field(12, default=False)
    color_temperature: float = field(13, default=0.0)
    has_transition_length: bool = field(14, default=False)
    transition_length: int32 = field(15, default=int32(0))
    has_flash_length: bool = field(16, default=False)
    flash_length: int32 = field(17, default=int32(0))
    has_effect: bool = field(18, default=False)
    effect: str = field(19, default='')


@message
@dataclass
class LightStateResponse(BaseMessage):
    type_: ClassVar[int] = 24


@message
@dataclass
class ListEntitiesRequest(BaseMessage):
    type_: ClassVar[int] = 11


@message
@dataclass
class BaseEntityResponse(BaseMessage):
    object_id: str = field(1)
    key: fixed32 = field(2)
    name: str = field(3)
    unique_id: str = field(4)


@message
@dataclass
class ListEntitiesLightResponse(BaseEntityResponse):
    type_: ClassVar[int] = 15

    supports_brightness: bool = field(5, default=False)
    supports_rgb: bool = field(6, default=False)
    supports_white_value: bool = field(7, default=False)
    supports_color_temperature: bool = field(8, default=False)
    min_mireds: float = field(9, default=0.0)
    max_mireds: float = field(10, default=0.0)
    effects: List[str] = field(11, default_factory=list)


@message
@dataclass
class ListEntitiesSensorResponse(BaseEntityResponse):
    type_: ClassVar[int] = 16


@message
@dataclass
class ListEntitiesDoneResponse(BaseMessage):
    type_: ClassVar[int] = 19


def recv_varint() -> Iterable[int]:
    while True:
        byte_, = socket_.recv(1)
        yield byte_
        if not byte_ & 0x80:
            break


def send(request: Message):
    print(f'Request: {request}')
    payload = request.dumps()
    socket_.sendall(
        PREAMBLE
        + unsigned_varint_serializer.dumps(len(payload))
        + unsigned_varint_serializer.dumps(request.type_)
        + payload
    )


def receive(response_type: Type[Message]) -> Message:
    assert socket_.recv(1) == PREAMBLE
    message_length = unsigned_varint_serializer.loads(bytes(recv_varint()))
    type_ = unsigned_varint_serializer.loads(bytes(recv_varint()))
    assert type_ == response_type.type_, type_
    response = response_type.loads(socket_.recv(message_length))
    print(f'Response: {response}')
    return response


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_:
    socket_.connect(('molgan.local', 6053))
    send(HelloRequest(client_info='molgan.py'))
    receive(HelloResponse)
    send(ConnectRequest())
    receive(ConnectResponse)
    send(ListEntitiesRequest())
    response = receive(ListEntitiesLightResponse)
    receive(ListEntitiesSensorResponse)
    receive(ListEntitiesDoneResponse)
    send(LightCommandRequest(
        key=response.key,
        has_state=True,
        state=True,
        has_rgb=True,
        red=1.0,
        green=0.7,
        blue=0.4,
        has_brightness=True,
        brightness=1.0,
        has_effect=True,
        effect='None',
    ))
    sleep(0.5)
