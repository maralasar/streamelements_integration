import enum

MOCK_URL = "https://stoplight.io/mocks/streamelements/api-docs/75539"


class Endpoints(enum.StrEnum):
    ACTIVITIES = enum.auto()
    CHANNELS = enum.auto()
    TIPS = enum.auto()


class ActivityKinds(enum.StrEnum):
    FOLLOW = enum.auto()
    TIP = enum.auto()
    SPONSOR = enum.auto()
    SUPERCHAT = enum.auto()  # Only YouTube?
    HOST = enum.auto()
    RAID = enum.auto()
    SUBSCRIBER = enum.auto()
    CHEER = enum.auto()
    REDEMPTION = enum.auto()  # Only for Streamelements own redeem system
    MERCH = enum.auto()  # Only YouTube?
