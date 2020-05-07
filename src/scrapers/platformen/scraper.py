import sys
from typing import List

from models.database import Db
from models.initiatives import Platform, BatchImportState, ImportBatch, InitiativeImport


class ScrapeException(Exception):
    pass


class PlatformSource(object):
    """
    Implementations should this class should are doing the real
    scraping of data.
    """

    def __iter__(self) -> InitiativeImport:
        """
        Lists bare initiatives from an Api or web page.
        """
        yield None

    def complete(self, initiative: InitiativeImport):
        """
        Completes the initiative provided by the iterator.
        This leaves error handling and completion strategy
        to the caller.
        """
        pass


class Scraper:
    """
    Concept for a base class that defines and deals basic setup of a scraper 
    """
    _sources: List[PlatformSource]

    limit: int = 5
    """Limits the iteration if a debugger is attached"""

    def __init__(self, platform_url: str, name: str, code: str, sources: List[PlatformSource]) -> object:
        if len(sources) == 0:
            raise ValueError("Expecting at least one source!")

        self._batch = None
        self.platform_url = platform_url
        self.name = name
        self.code = code
        self._sources = sources
        self._db = Db()

    def scrape(self):
        """
        Starts the scraping of given platform.
        This is all synchronous. Although this does help not flooding
        a web server even faster is does make it all a lot slower.
        """
        print(f"starting {self.name} ({self.code}) scraper")
        self._start_batch()

        try:
            for source in self._sources:
                for initiative in source:
                    source.complete(initiative)
                    self._batch.initiatives.append(initiative)
        except ScrapeException:
            self._batch.state = BatchImportState.FAILED
        else:
            self._batch.state = BatchImportState.IMPORTED

        self.save_batch()

    def _start_batch(self):
        platform = self.load_platform()
        self._batch = ImportBatch.start_new(platform)
        self.save_batch()

    def should_continue(self, count):
        """
        Method for debugging purposes only
        """
        if sys.gettrace() is not None:
            return count < self.limit
        else:
            return True

    def load_platform(self):
        """ retrieve platform instance or create it """
        platform = self.get_platform()
        if platform is None:
            platform = Platform(name=self.name,
                                url=self.platform_url,
                                place='Nederland')
            self._db.session.add(platform)
            # we can also raise exception or create default instance.
            # raise Exception("No platform found")

        return platform

    def get_platform(self):
        return self._db.session.query(Platform).filter(Platform.url.like('%' + self.platform_url + '%')).first()

    def get_current_batch(self) -> ImportBatch:
        return self._batch

    def add_source(self, source: PlatformSource):
        if source is None:
            raise ValueError("source is None")
        self._sources.append(source)

    def save_batch(self):
        if self._batch is None:
            return

        if self._batch.id is None:
            self._db.session.add(self._batch)

        self._db.session.commit()


class ScraperConcept(Scraper):
    """This is conceptual code for discussion purposes to go in Scraper class"""
    def start_scrape(self):
        try:
            platform = self.load_platform()
            # start batch
            batch = ImportBatch.start_new(platform)
            self._db.session.add(batch)
            self._db.session.commit()
        except Exception as e:
            print("Error while scraping: " + e.args[0])
            # TODO: Log and raise wrapped exception

        try:
            # This is not perfect given the NL voor Elkaar also uses a configuration object
            # because actually runs two separate scraping sessions for supply and demand
            self.scrape_list(self._batch)
        except Exception as e:
            self._batch.state = BatchImportState.FAILED
            print("Error while scraping: " + e.args[0])
            # TODO: Should do logging here
        else:
            self._batch.state = BatchImportState.IMPORTED

        self._batch.stopped_at = datetime.datetime.now(datetime.timezone.utc)

        self._db.session.commit()

    def scrape_list(self, batch):
        """
        Scrapes all initiatives and adds them to the batch.
        """
        has_more = True
        initiatives = []
        while has_more:
            current_initiatives = self.get_items(batch)
            if not current_initiatives:
                has_more = False
                continue

            for initiative in current_initiatives:
                self.scrape_item(initiative)
                if initiative is not None:
                    batch.initiatives.append(initiative)


    def get_items(self, batch):
        """
        Do HTTP Request, handle errors and return skeleton Import.
        This needs to hold some state given it will be called multiple times
        Assuming for instance paging is used to retrieve a list of all items.
        This implies state needs to be reset for each batch or we hold te state on
        the Batch itself. I have no idea if we can dynamically add attributes
        that simply are used only for a specific scraper.
        """
        return #[InitiativeImport()]

    def scrape_item(self, batch, item):
        """
        Do HTTP Request, handle error and scrape detail information of initiative.
        POssible the scraping can be deferred to the TreeParser or any other class
        """
        return item