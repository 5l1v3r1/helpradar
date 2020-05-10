import logging
from collections import namedtuple
from typing import Generator

import requests
import json

from models.initiatives import InitiativeImport, InitiativeGroup
from .scraper import Scraper, PlatformSource, PlatformSourceConfig


class WijAmsterdamSource(PlatformSource):
    """
    Very trivial source. Reads all ideas from Wij Amsterdam open api
    and returns them immediately
    """
    def __init__(self):
        super().__init__(PlatformSourceConfig(
            "https://www.wijamsterdam.nl",
            "https://api2.openstad.amsterdam/api/site/197/idea",
            None
        ))

    def initiatives(self) -> Generator[InitiativeImport, None, None]:
        response = self.get(self.config.list_endpoint)

        data = json.loads(
            response.content,
            object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

        for item in data:
            initiative = InitiativeImport(
                source_id=item.id,
                source_uri=f"https://wijamsterdam.nl/initiatief/{item.id}",
                created_at=item.createdAt,
                name=item.title,
                description=f"{item.summary}"
                            f"\n--------\n"
                            f"{item.description}",
                group=InitiativeGroup.SUPPLY,
                url=item.extraData.isOrganiserWebsite
            )
            if hasattr(item, "position"):
                initiative.latitude = item.position.lat
                initiative.longitude = item.position.lng
            yield initiative

    def complete(self, initiative: InitiativeImport):
        pass


class WijAmsterdam(Scraper):

    def __init__(self):
        source = WijAmsterdamSource()
        super().__init__(
            source.config.platform_url,
            "Wij Amsterdam",
            "wams",
            [source])

    def get_logger(self) -> logging.Logger:
        return logging.getLogger(__name__)
