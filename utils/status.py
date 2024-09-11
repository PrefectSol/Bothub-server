from enum import Enum


class StatusCode(Enum):
    Unknown = -1
    Success = 0
    Finished = 1
    StopSignal = 2
    LoadConfigError = 3
    UnknownUser = 4
    InvalidSignature = 5
    InvalidPermissions = 6
    FailedCreateHost = 7
    FailedCreateUserClass = 8
    InternalGameError = 9
    HostNotFound = 10
    AddBotError = 11
    SendDataError = 12
    CommunicationError = 13
    TimeOut = 14
    GameStarted = 15
    ConnectionClosed = 16
    GameRunning = 17
    UnknownHost = 18
    Accepted = 19
    Rejected = 20
    GameFinished = 21


class HttpCode(Enum):
    Continue = 100
    Ok = 200
    BadRequest = 400
    NotFound = 404
    Gone = 410
    InternalServerError = 500
    ServiceUnvaliable = 503
