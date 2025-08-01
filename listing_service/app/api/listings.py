# API endpoints for listing management (CRUD operations and search)
from fastapi import APIRouter, HTTPException, Query
from pymongo.errors import DuplicateKeyError
from app.crud import (  create_listing, get_listing_by_id, 
                        update_listing, delete_listing, search_listings, 
                        get_listings_paginated, get_listings_for_user)
from app.models.listing_models import Listing, Create, DetailedList
from typing import List, Optional


router = APIRouter(prefix="/listings", tags=["listings"])

@router.post("/", response_model=Create)
async def create_listing_endpoint(house: Create):
    try:
        listings = await create_listing(house.to_mongo_dict())
        return listings
    except DuplicateKeyError:
        # Handle gracefully if same name used twice
        raise HTTPException(status_code=400, detail="Listing with same name already exists.")


@router.get("/search", response_model=List[Listing])
async def search_listings_endpoint(
    page: int = 1,
    limit: int = 10,
    name: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    sort_by: Optional[str] = None,
    sort_order: Optional[int] = 1
):
    filters = {}
    if name:
        filters["name"] = {"$regex": name, "$options": "i"}
    if property_type:
        filters["property_type"] = property_type
    if min_price is not None or max_price is not None:
        filters["price"] = {}
        if min_price is not None:
            filters["price"]["$gte"] = min_price
        if max_price is not None:
            filters["price"]["$lte"] = max_price

    listings = await search_listings(filters, page, limit, sort_by, sort_order)
    for listing in listings:
        if "summary" not in listing:
            listing["summary"] = f"A beautiful {listing.get('property_type', 'property')} in {listing.get('address', {}).get('market', 'a great location')}"
    return listings

@router.get("/", response_model=List[Listing])
async def get_listings_paginated_endpoint(page: int = 1, limit: int = 10):
    listings = await get_listings_paginated(page, limit)
    return listings

@router.get("/{item_id}", response_model=List[DetailedList])
async def get_listing_by_id_endpoint(item_id: str):
    listings = await get_listing_by_id(item_id)
    return listings

@router.put("/{item_id}", response_model=Create)
async def update_listing_endpoint(item_id: str, updated_listing: Create):
    updated = await update_listing(item_id, updated_listing)
    return updated

@router.delete("/{item_id}")
async def delete_listing_endpoint(item_id: str):
    deleted = await delete_listing(item_id)
    if deleted:
        return {"message": "Listing deleted"}
    raise HTTPException(status_code=404, detail="Listing not found")

@router.get("/user/{user_id}", response_model=List[Listing])
async def get_listings_for_user_endpoint(user_id: str):
    listings = await get_listings_for_user(user_id)
    return listings