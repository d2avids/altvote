from __future__ import annotations
from typing import TYPE_CHECKING
from django.utils import timezone
if TYPE_CHECKING:
    from polls.models import Poll


def poll_end_datetime_passed(poll: Poll) -> bool:
    return timezone.now() > poll.end_datetime
