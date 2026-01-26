from typing import Generic, TypeVar, List
from ninja import Schema, Field

# Generic type for items in paginated response
T = TypeVar('T')


class PaginationParams(Schema):
    """Query parameters for pagination"""
    page: int = Field(1, ge=1, description="Page number (starts from 1)")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page (max 100)")


class PaginatedResponse(Schema, Generic[T]):
    """Generic paginated response schema"""
    items: List[T]
    count: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
