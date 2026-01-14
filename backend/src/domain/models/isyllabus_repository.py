from abc import ABC, abstractmethod
from typing import List, Optional
from .syllabus import Syllabus


class ISyllabusRepository(ABC):
    @abstractmethod
    def add(self, syllabus: Syllabus) -> Syllabus:
        pass

    @abstractmethod
    def get_by_id(self, syllabus_id: int) -> Optional[Syllabus]:
        pass

    @abstractmethod
    def list(self) -> List[Syllabus]:
        pass
    
    @abstractmethod
    def list_by_owner(self, owner_lecturer_id: int) -> List[Syllabus]:
        """List all syllabi owned by a specific lecturer."""
        pass
    
    @abstractmethod
    def list_by_status(self, status: str) -> List[Syllabus]:
        """List all syllabi with a specific lifecycle status."""
        pass

    @abstractmethod
    def update(self, syllabus: Syllabus) -> Syllabus:
        pass

    @abstractmethod
    def delete(self, syllabus_id: int) -> None:
        pass

    @abstractmethod
    def create_initial_version(self, syllabus: Syllabus, created_by_user_id: int) -> Syllabus:
        """Create initial SyllabusVersion (version_no=1) and link it to syllabus."""
        pass
