import json
import logging

from datetime import datetime, timedelta, timezone

from typing import Any

import iso8601

logger = logging.getLogger("aw.client.models")


class Event(dict):
    """
    Used to represents an event.
    """

    # TODO: Use JSONSchema as specification
    # FIXME: tags and label have similar/same meaning, pick one
    # FIXME: Some other databases (such as Zenobase) use tag instead of label, we should consider changing
    ALLOWED_FIELDS = {
        "timestamp": datetime,
        "count": int,
        "duration": dict,
        "label": str,
        "note": str,
    }

    def __init__(self, **kwargs: Any) -> None:
        dict.__init__(self, **kwargs)
        self.validate()

    def validate(self) -> None:
        # Remove invalid keys
        for k, v in list(self.items()):
            if k not in self.ALLOWED_FIELDS:
                self.pop(k)
                logger.warning("Removed invalid field {} from event: {}".format(k, self))

        # Listify all non-list items
        for k, v in self.items():
            if not isinstance(v, list):
                self[k] = [v]

        # Validate timestamp
        if "timestamp" not in self:
            logger.warning("Event did not have a timestamp, using now as timestamp")
            self["timestamp"] = [datetime.now(timezone.utc)]
        for i, ts in enumerate(self["timestamp"]):
            if isinstance(ts, str):
                ts = iso8601.parse_date(ts)
            # Set resolution to milliseconds instead of microseconds
            # (Fixes incompability with software based on unix time, for example mongodb)
            ts = ts.replace(microsecond=int(ts.microsecond / 1000) * 1000)
            # Add timezone if not set
            if not ts.tzinfo:
                # Needed? All timestamps should be iso8601 so ought to always contain timezone.
                # Yes, because it is optional in iso8601
                logger.warning("timestamp without timezone found, using UTC: {}".format(ts))
                ts = ts.replace(tzinfo=timezone.utc)
            self["timestamp"][i] = ts

        # Validate duration
        if "duration" in self:
            self["duration"] = [{"value": td.total_seconds(), "unit": "s"}
                                if isinstance(td, timedelta) else td
                                for td in self["duration"]]

        # Check for invalid types
        for k in self.keys():
            for i, v in reversed(list(enumerate(self[k]))):
                if not isinstance(v, self.ALLOWED_FIELDS[k]):
                    logger.error("Found value {} in field {} that was not of proper instance ({}, expected: {}). Event: {}".format(v, k, type(v), self.ALLOWED_FIELDS[k], self))
                    self[k].pop(i)

        # Remove empty lists
        for k in list(self.keys()):
            if not self[k]:
                del self[k]

    def to_json_dict(self) -> dict:
        """Useful when sending data over the wire.
        Any mongodb interop should not use do this as it accepts datetimes."""
        data = self.copy()
        data["timestamp"] = [dt.astimezone().isoformat() for dt in data["timestamp"]]
        return data

    def to_json_str(self) -> str:
        data = self.to_json_dict()
        return json.dumps(data)
