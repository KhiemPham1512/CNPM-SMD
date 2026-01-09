from abc import ABC, abstractmethod
from typing import List, Optional
from .subject import Subject


class ISubjectRepository(ABC):
    @abstractmethod
    def add(self, subject: Subject) -> Subject:
        pass

    @abstractmethod
    def get_by_id(self, subject_id: int) -> Optional[Subject]:
        pass

    @abstractmethod
    def list(self) -> List[Subject]:
        pass

    @abstractmethod
    def update(self, subject: Subject) -> Subject:
        pass

    @abstractmethod
    def delete(self, subject_id: int) -> None:
        pass

