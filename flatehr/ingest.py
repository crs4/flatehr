import abc
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pprint import pprint
from typing import Dict, Iterable, Tuple, Union

import tqdm
from tqdm.contrib.concurrent import thread_map

from .flat import Composition, WebTemplateNode, diff
from .http import HTTPException, OpenEHRClient

logger = logging.getLogger()

SUCCESS = int
FAIL = int
CORRUPTED = int


@dataclass
class EHRCompositionMapping:
    composition: Composition
    ehr_id: str


EHRCompositionMappings = Iterable[EHRCompositionMapping]


@dataclass
class Ingester(abc.ABC):
    @abc.abstractmethod
    def ingest(
        self,
        ehr_compositions: EHRCompositionMappings,
    ) -> Tuple[SUCCESS, FAIL]:
        ...


@dataclass
class BasicIngester(Ingester):
    client: OpenEHRClient
    dump_composition: bool = False
    save_diff: bool = False

    def ingest(
        self,
        ehr_compositions: EHRCompositionMappings,
    ) -> Tuple[SUCCESS, FAIL]:
        success = fail = 0
        for ehr_composition in ehr_compositions:
            try:
                self._ingest(ehr_composition)
                success += 1
            except Exception as ex:
                logger.exception(ex)
                fail += 1
        return (success, fail)

    def _ingest(self, ehr_composition: EHRCompositionMapping) -> str:
        ehr_id = ehr_composition.ehr_id
        composition = ehr_composition.composition

        if self.dump_composition:
            self._dump_composition(composition, ehr_id)

        try:
            comp_id = self.client.post_composition(composition, ehr_id)
        except HTTPException as ex:
            raise RuntimeError(
                f"failed posting composition {composition}, error: {ex}"
            ) from ex
        #  logger.info("patient %s-> composition %s", external_id, comp_id)

        if self.save_diff:
            self._save_diff(composition, comp_id)
        return comp_id

    def _dump_composition(
        self,
        composition: Composition,
        external_id: str,
        dirname: str = "compositions",
    ):
        os.makedirs(dirname, exist_ok=True)
        dump_filename = f"{dirname}/{external_id}.json"
        logger.info("dumping composition %s to %s", composition, dump_filename)
        with open(dump_filename, "w") as f_obj:
            json.dump(composition.as_flat(), f_obj)

    def _save_diff(
        self,
        composition: Composition,
        composition_id: str,
        dirname: str = "diff",
    ):
        saved = self.client.get_composition(composition_id)
        os.makedirs(dirname, exist_ok=True)
        diff_from_posted = diff(composition.as_flat(), saved)
        diff_filename = f"{dirname}/{composition_id}.diff"
        logger.info("dumping diff to %s", diff_filename)
        with open(diff_filename, "w") as f_obj:
            pprint(diff_from_posted, f_obj, indent=2)

        dump_db_filename = f"{composition_id}.db.json"
        logger.info("dumping db composition to %s", dump_db_filename)
        with open(dump_db_filename, "w") as f_obj:
            json.dump(saved, f_obj)


@dataclass
class MultiThreadedIngester(BasicIngester):
    max_workers: int = None

    def ingest(
        self,
        ehr_compositions: EHRCompositionMappings,
    ) -> Tuple[SUCCESS, FAIL]:
        success = fail = 0
        compositions_ok = []
        try:
            for comp in ehr_compositions:
                compositions_ok.append(comp)
        except Exception as ex:
            logger.exception(ex)
            fail += 1

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            try:

                for _ in executor.map(self._ingest, compositions_ok):
                    success += 1
            except Exception as ex:
                logger.exception(ex)
                fail += 1
        return (success, fail)


def multi_source_ingestion(
    ingester: Ingester,
    ehr_compositions: Iterable[EHRCompositionMappings],
    multithread: bool = True,
    max_workers: int = None,
) -> Tuple[SUCCESS, FAIL]:
    success = fail = 0
    if multithread:
        results = thread_map(
            ingester.ingest,
            list(ehr_compositions),
            max_workers=max_workers,
        )

    else:
        results = [
            ingester.ingest(ehr_composition)
            for ehr_composition in tqdm.tqdm(list(ehr_compositions))
        ]

    for res in results:
        success += res[0]
        fail += res[1]
    return success, fail


class CompositionFactory(abc.ABC):
    @abc.abstractmethod
    def get_compositions(self) -> Iterable[Composition]:
        ...


VALUE = Union[float, str]
KWARGS = Dict[str, VALUE]


class ValueConverter(abc.ABC):
    @abc.abstractmethod
    def convert(self, web_template_node: WebTemplateNode, value) -> KWARGS:
        ...

    @abc.abstractmethod
    def accepted_data_types(self) -> Tuple[str]:
        ...
