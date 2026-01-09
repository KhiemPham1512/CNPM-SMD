"""
Password hashing interface for domain layer.

This interface allows the service layer to use password hashing
without depending on specific infrastructure implementations.
"""
from abc import ABC, abstractmethod


class IPasswordHasher(ABC):
    """Interface for password hashing operations."""
    
    @abstractmethod
    def hash_password(self, plain_password: str) -> str:
        """
        Hash a plain text password.
        
        Args:
            plain_password: Plain text password to hash
            
        Returns:
            Hashed password string
        """
        pass
    
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a hashed password.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        pass
