Okay, let's break down the implementation status of Feature 4 and provide the necessary code.

**1) Explain if this is already complete, or what is missing**

This feature is **not complete**. Based on the provided source code, none of the core components described in the goal have been implemented yet.

**What is Missing:**

1.  **Backend Model:** The `VendorClassificationCache` SQLAlchemy model needs to be created.
2.  **Database Migration/Table Creation:** The `vendor_classification_cache` table needs to be added to the database schema (likely handled by `Base.metadata.create_all` if the model is imported correctly during initialization).
3.  **Cache Population Logic:** The job completion logic in `app/tasks/classification_tasks.py` (specifically within `_process_vendor_file_async` and potentially `_process_reclassification_async` or the `Job.complete` method) needs to be modified to identify high-confidence/reviewed results and write them to the cache table.
4.  **Cache Query Logic:** The `process_vendors` function in `app/tasks/classification_logic.py` needs to be modified to query the cache *before* starting the standard classification workflow and use cached results when found.
5.  **Admin API Endpoints:** New API endpoints under `/api/v1/admin/cache/` need to be created (likely in a new router file, e.g., `app/api/admin.py`).
6.  **Admin API Router Inclusion:** The new admin router needs to be included in `app/api/main.py`.
7.  **Frontend Admin View:** A new Vue component (e.g., `AdminClassificationCache.vue`) is required to display the cache data.
8.  **Frontend Routing:** A new route needs to be added in the Vue router to display the admin cache component.
9.  **Frontend Navigation:** A link to the new admin cache view needs to be added to the admin interface (e.g., in a sidebar or potentially modifying `UserManagement.vue`'s parent layout/view).
10. **Frontend API Service:** New functions need to be added to `frontend/vue_frontend/src/services/api.ts` to interact with the new admin cache API endpoints.

**2) Provide the COMPLETE code for any NEW files needed.**

```python
# <file path='app/models/vendor_classification_cache.py'>
import enum
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum as SQLAlchemyEnum, Index, UniqueConstraint
from sqlalchemy.sql import func
from core.database import Base
from datetime import datetime, timezone

class CacheClassificationSource(enum.Enum):
    INITIAL_HIGH_CONFIDENCE = "Initial-HighConfidence"
    SEARCH_HIGH_CONFIDENCE = "Search-HighConfidence"
    REVIEW_CONFIRMED = "Review-Confirmed"
    ADMIN_MANUAL = "Admin-Manual" # For potential future use

class VendorClassificationCache(Base):
    """
    Stores high-confidence or manually verified vendor classifications to avoid redundant processing.
    """
    __tablename__ = "vendor_classification_cache"

    # Use normalized_vendor_name as the primary key for efficient lookups
    normalized_vendor_name = Column(String, primary_key=True, index=True)

    target_level_achieved = Column(Integer, nullable=False, comment="The deepest level successfully classified (1-5)")

    level1_id = Column(String, nullable=True)
    level1_name = Column(String, nullable=True)
    level2_id = Column(String, nullable=True)
    level2_name = Column(String, nullable=True)
    level3_id = Column(String, nullable=True)
    level3_name = Column(String, nullable=True)
    level4_id = Column(String, nullable=True)
    level4_name = Column(String, nullable=True)
    level5_id = Column(String, nullable=True)
    level5_name = Column(String, nullable=True)

    final_confidence = Column(Float, nullable=True, comment="Confidence score at the target_level_achieved")
    final_status = Column(String, nullable=False, default="Classified", comment="Should always be 'Classified' for cached entries") # Status when cached

    classification_source = Column(SQLAlchemyEnum(CacheClassificationSource), nullable=False, comment="How this cached entry was originally determined")
    job_id_origin = Column(String, nullable=False, comment="The job ID that resulted in this cached entry")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Optional: Add a unique constraint if needed, though primary key handles this
    # __table_args__ = (UniqueConstraint('normalized_vendor_name', name='uq_vendor_cache_name'),)

    def __repr__(self):
        return f"<VendorClassificationCache(name='{self.normalized_vendor_name}', source='{self.classification_source.value}', updated='{self.last_updated_at}')>"

```

```python
# <file path='app/schemas/admin.py'>
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.vendor_classification_cache import CacheClassificationSource # Import the enum

class VendorCacheItemBase(BaseModel):
    normalized_vendor_name: str
    target_level_achieved: int
    level1_id: Optional[str] = None
    level1_name: Optional[str] = None
    level2_id: Optional[str] = None
    level2_name: Optional[str] = None
    level3_id: Optional[str] = None
    level3_name: Optional[str] = None
    level4_id: Optional[str] = None
    level4_name: Optional[str] = None
    level5_id: Optional[str] = None
    level5_name: Optional[str] = None
    final_confidence: Optional[float] = None
    final_status: str # Should always be 'Classified'
    classification_source: CacheClassificationSource # Use the enum
    job_id_origin: str
    created_at: datetime
    last_updated_at: datetime

class VendorCacheItemResponse(VendorCacheItemBase):
    class Config:
        from_attributes = True # Pydantic V2 alias for orm_mode

class PaginatedVendorCacheResponse(BaseModel):
    total: int
    items: List[VendorCacheItemResponse]
    page: int
    size: int
    pages: int

# Add schemas for potential PUT/POST later if needed
# class VendorCacheUpdate(BaseModel):
#     # Define fields admins can update
#     level1_id: Optional[str] = None
#     # ... etc.
#     classification_source: Optional[CacheClassificationSource] = CacheClassificationSource.ADMIN_MANUAL

```

```python
# <file path='app/api/admin.py'>
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import func, or_ # Import 'or_' for search
from typing import List, Optional

from core.database import get_db
from api.auth import get_current_active_superuser
from models.user import User
from models.vendor_classification_cache import VendorClassificationCache, CacheClassificationSource
from schemas.admin import VendorCacheItemResponse, PaginatedVendorCacheResponse

router = APIRouter()

# Dependency for the entire router to ensure only superusers can access
# Apply this when including the router in main.py instead of here per endpoint
# dependencies=[Depends(get_current_active_superuser)]

CACHE_DEFAULT_PAGE_SIZE = 50
CACHE_MAX_PAGE_SIZE = 200

@router.get(
    "/cache/",
    response_model=PaginatedVendorCacheResponse,
    summary="List Cached Vendor Classifications (Admin Only)",
    dependencies=[Depends(get_current_active_superuser)] # Apply dependency here
)
async def list_cached_vendors(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search term for vendor name or NAICS code/name"),
    source: Optional[CacheClassificationSource] = Query(None, description="Filter by classification source"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(CACHE_DEFAULT_PAGE_SIZE, ge=1, le=CACHE_MAX_PAGE_SIZE, description="Items per page"),
    # current_user: User = Depends(get_current_active_superuser) # Already handled by dependency
):
    """
    Retrieves a paginated list of cached vendor classifications.
    Allows filtering by search term (name, NAICS ID/Name) and classification source.
    Requires superuser privileges.
    """
    skip = (page - 1) * size
    query = db.query(VendorClassificationCache)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(VendorClassificationCache.normalized_vendor_name).like(search_term),
                func.lower(VendorClassificationCache.level1_id).like(search_term),
                func.lower(VendorClassificationCache.level1_name).like(search_term),
                func.lower(VendorClassificationCache.level2_id).like(search_term),
                func.lower(VendorClassificationCache.level2_name).like(search_term),
                func.lower(VendorClassificationCache.level3_id).like(search_term),
                func.lower(VendorClassificationCache.level3_name).like(search_term),
                func.lower(VendorClassificationCache.level4_id).like(search_term),
                func.lower(VendorClassificationCache.level4_name).like(search_term),
                func.lower(VendorClassificationCache.level5_id).like(search_term),
                func.lower(VendorClassificationCache.level5_name).like(search_term)
            )
        )

    if source:
        query = query.filter(VendorClassificationCache.classification_source == source)

    total_count = query.count()
    items = query.order_by(VendorClassificationCache.last_updated_at.desc()).offset(skip).limit(size).all()

    total_pages = (total_count + size - 1) // size if size > 0 else 0

    return PaginatedVendorCacheResponse(
        total=total_count,
        items=items,
        page=page,
        size=size,
        pages=total_pages
    )


@router.get(
    "/cache/{normalized_vendor_name}",
    response_model=VendorCacheItemResponse,
    summary="Get Specific Cached Vendor Classification (Admin Only)",
    dependencies=[Depends(get_current_active_superuser)] # Apply dependency here
)
async def get_cached_vendor(
    normalized_vendor_name: str = Path(..., description="The normalized name of the vendor to retrieve"),
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_superuser) # Already handled by dependency
):
    """
    Retrieves a single cached vendor classification by its normalized name.
    Requires superuser privileges.
    """
    cache_entry = db.query(VendorClassificationCache).filter(
        VendorClassificationCache.normalized_vendor_name == normalized_vendor_name
    ).first()

    if not cache_entry:
        raise HTTPException(status_code=404, detail="Cached vendor not found")

    return cache_entry

# --- Placeholder for future Admin actions ---
# @router.put(
#     "/cache/{normalized_vendor_name}",
#     response_model=VendorCacheItemResponse,
#     summary="Update Cached Vendor Classification (Admin Only - Future)",
#     dependencies=[Depends(get_current_active_superuser)]
# )
# async def update_cached_vendor(
#     normalized_vendor_name: str = Path(..., description="The normalized name of the vendor to update"),
#     update_data: VendorCacheUpdate, # Need to define this schema
#     db: Session = Depends(get_db),
# ):
#     """ (Future Implementation) Updates a specific cached vendor entry. """
#     cache_entry = db.query(VendorClassificationCache).filter(
#         VendorClassificationCache.normalized_vendor_name == normalized_vendor_name
#     ).first()
#     if not cache_entry:
#         raise HTTPException(status_code=404, detail="Cached vendor not found")
#     # ... update logic ...
#     # update_data_dict = update_data.model_dump(exclude_unset=True)
#     # for key, value in update_data_dict.items():
#     #     setattr(cache_entry, key, value)
#     # cache_entry.classification_source = CacheClassificationSource.ADMIN_MANUAL # Force source
#     # cache_entry.last_updated_at = func.now() # Let DB handle onupdate
#     # db.commit()
#     # db.refresh(cache_entry)
#     # return cache_entry
#     raise HTTPException(status_code=501, detail="Update not yet implemented")

# @router.delete(
#     "/cache/{normalized_vendor_name}",
#     status_code=204,
#     summary="Delete Cached Vendor Classification (Admin Only - Future)",
#     dependencies=[Depends(get_current_active_superuser)]
# )
# async def delete_cached_vendor(
#     normalized_vendor_name: str = Path(..., description="The normalized name of the vendor to delete"),
#     db: Session = Depends(get_db),
# ):
#     """ (Future Implementation) Deletes a specific cached vendor entry. """
#     cache_entry = db.query(VendorClassificationCache).filter(
#         VendorClassificationCache.normalized_vendor_name == normalized_vendor_name
#     ).first()
#     if not cache_entry:
#         raise HTTPException(status_code=404, detail="Cached vendor not found")
#     # db.delete(cache_entry)
#     # db.commit()
#     # return None
#     raise HTTPException(status_code=501, detail="Delete not yet implemented")

```

```vue
<!-- <file path='frontend/vue_frontend/src/components/AdminClassificationCache.vue'> -->
<template>
  <div class="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
    <div class="bg-gray-100 text-gray-800 p-4 sm:p-5 border-b border-gray-200">
      <h4 class="text-xl font-semibold mb-0">Internal Classification Cache</h4>
      <p class="text-sm text-gray-600 mt-1">View high-confidence classifications stored for optimization. (Read-Only)</p>
    </div>

    <div class="p-6 sm:p-8">
      <!-- Filters -->
      <div class="mb-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label for="cache-search" class="block text-sm font-medium text-gray-700 mb-1">Search Name/Code:</label>
          <input
            type="text"
            id="cache-search"
            v-model="filters.search"
            placeholder="e.g., Acme Corp, 541511"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary text-sm"
          />
        </div>
        <div>
          <label for="cache-source" class="block text-sm font-medium text-gray-700 mb-1">Source:</label>
          <select
            id="cache-source"
            v-model="filters.source"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary text-sm bg-white"
          >
            <option value="">All Sources</option>
            <option v-for="src in cacheSources" :key="src" :value="src">{{ formatSource(src) }}</option>
          </select>
        </div>
         <div>
          <label for="cache-size" class="block text-sm font-medium text-gray-700 mb-1">Items per page:</label>
          <select
            id="cache-size"
            v-model="pagination.size"
            @change="handleSizeChange"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary text-sm bg-white"
          >
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
            <option value="200">200</option>
          </select>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center text-gray-500 py-8">
        <svg class="animate-spin inline-block h-6 w-6 text-primary mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Loading cache entries...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="p-4 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm flex items-center">
        <ExclamationTriangleIcon class="h-5 w-5 mr-2 text-red-600 flex-shrink-0"/>
        <span>Error loading cache: {{ error }}</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="!cacheEntries || cacheEntries.length === 0" class="text-center text-gray-500 py-8">
        <p>No cache entries found matching your criteria.</p>
      </div>

      <!-- Cache Table -->
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Vendor Name (Normalized)</th>
              <th scope="col" class="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Classification (L1-L5)</th>
              <th scope="col" class="px-3 py-2 text-center font-medium text-gray-500 uppercase tracking-wider">Level</th>
              <th scope="col" class="px-3 py-2 text-center font-medium text-gray-500 uppercase tracking-wider">Conf.</th>
              <th scope="col" class="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Source</th>
              <th scope="col" class="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Origin Job</th>
              <th scope="col" class="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Last Updated</th>
              <!-- <th scope="col" class="px-3 py-2 text-right font-medium text-gray-500 uppercase tracking-wider">Actions</th> -->
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="entry in cacheEntries" :key="entry.normalized_vendor_name" class="hover:bg-gray-50">
              <td class="px-3 py-2 whitespace-nowrap font-medium text-gray-900">{{ entry.normalized_vendor_name }}</td>
              <td class="px-3 py-2">
                <div class="text-xs text-gray-500">
                  <span v-if="entry.level1_id">L1: {{ entry.level1_id }} {{ entry.level1_name ? `(${entry.level1_name})` : '' }}</span><br v-if="entry.level2_id"/>
                  <span v-if="entry.level2_id">L2: {{ entry.level2_id }} {{ entry.level2_name ? `(${entry.level2_name})` : '' }}</span><br v-if="entry.level3_id"/>
                  <span v-if="entry.level3_id">L3: {{ entry.level3_id }} {{ entry.level3_name ? `(${entry.level3_name})` : '' }}</span><br v-if="entry.level4_id"/>
                  <span v-if="entry.level4_id">L4: {{ entry.level4_id }} {{ entry.level4_name ? `(${entry.level4_name})` : '' }}</span><br v-if="entry.level5_id"/>
                  <span v-if="entry.level5_id">L5: {{ entry.level5_id }} {{ entry.level5_name ? `(${entry.level5_name})` : '' }}</span>
                  <span v-if="!entry.level1_id" class="text-gray-400 italic">No classification data</span>
                </div>
              </td>
              <td class="px-3 py-2 whitespace-nowrap text-center text-gray-600">{{ entry.target_level_achieved }}</td>
              <td class="px-3 py-2 whitespace-nowrap text-center text-gray-600">{{ formatConfidence(entry.final_confidence) }}</td>
              <td class="px-3 py-2 whitespace-nowrap text-gray-600">{{ formatSource(entry.classification_source) }}</td>
               <td class="px-3 py-2 whitespace-nowrap text-gray-500">
                 <router-link
                    v-if="entry.job_id_origin"
                    :to="{ name: 'JobDetails', params: { jobId: entry.job_id_origin } }"
                    class="text-primary hover:text-primary-hover hover:underline"
                    :title="`View Origin Job ${entry.job_id_origin}`"
                 >
                    {{ entry.job_id_origin.substring(0, 8) }}...
                 </router-link>
                 <span v-else>-</span>
               </td>
              <td class="px-3 py-2 whitespace-nowrap text-gray-500">{{ formatDateTime(entry.last_updated_at) }}</td>
              <!-- <td class="px-3 py-2 whitespace-nowrap text-right font-medium space-x-1">
                <button class="text-indigo-600 hover:text-indigo-800 disabled:opacity-50" title="Edit (Not Implemented)" disabled>
                  <PencilSquareIcon class="h-4 w-4 inline-block" />
                </button>
                <button class="text-red-600 hover:text-red-800 disabled:opacity-50" title="Delete (Not Implemented)" disabled>
                  <TrashIcon class="h-4 w-4 inline-block" />
                </button>
              </td> -->
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="pagination.totalPages > 1" class="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
        <div class="text-sm text-gray-700">
          Showing <span class="font-medium">{{ pagination.startItem }}</span>
          to <span class="font-medium">{{ pagination.endItem }}</span>
          of <span class="font-medium">{{ pagination.totalItems }}</span> results
        </div>
        <div class="flex space-x-1">
          <button
            @click="changePage(pagination.currentPage - 1)"
            :disabled="pagination.currentPage <= 1"
            class="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            v-for="page in pagination.pageNumbers"
            :key="page"
            @click="changePage(page)"
            :class="[
              'px-3 py-1 border border-gray-300 rounded-md text-sm font-medium',
              page === pagination.currentPage
                ? 'bg-primary text-white border-primary'
                : 'text-gray-700 bg-white hover:bg-gray-50'
            ]"
          >
            {{ page }}
          </button>
          <button
            @click="changePage(pagination.currentPage + 1)"
            :disabled="pagination.currentPage >= pagination.totalPages"
            class="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed } from 'vue';
import apiService, { type VendorCacheItem, type PaginatedVendorCacheResponse } from '@/services/api';
import { ExclamationTriangleIcon, PencilSquareIcon, TrashIcon } from '@heroicons/vue/24/outline';
import { debounce } from 'lodash-es'; // Using lodash for debouncing search input

// Backend enum values (must match app/models/vendor_classification_cache.py)
const cacheSources = [
    "Initial-HighConfidence",
    "Search-HighConfidence",
    "Review-Confirmed",
    "Admin-Manual"
];

const cacheEntries = ref<VendorCacheItem[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);

const filters = reactive({
  search: '',
  source: '',
});

const pagination = reactive({
  currentPage: 1,
  size: 50, // Default page size
  totalItems: 0,
  totalPages: 0,
  startItem: 0,
  endItem: 0,
  pageNumbers: [] as number[], // For displaying pagination controls
});

const fetchCacheEntries = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    const params = {
      page: pagination.currentPage,
      size: pagination.size,
      search: filters.search || undefined, // Send undefined if empty
      source: filters.source || undefined, // Send undefined if empty
    };
    const response: PaginatedVendorCacheResponse = await apiService.getCacheEntries(params);
    cacheEntries.value = response.items;
    pagination.totalItems = response.total;
    pagination.totalPages = response.pages;
    pagination.startItem = response.total > 0 ? (response.page - 1) * response.size + 1 : 0;
    pagination.endItem = Math.min(response.page * response.size, response.total);
    updatePageNumbers();

  } catch (err: any) {
    error.value = err.message || 'Failed to load cache entries.';
    cacheEntries.value = []; // Clear entries on error
    pagination.totalItems = 0;
    pagination.totalPages = 0;
  } finally {
    isLoading.value = false;
  }
};

const updatePageNumbers = () => {
    const maxPagesToShow = 5; // Max number of page buttons to show
    const currentPage = pagination.currentPage;
    const totalPages = pagination.totalPages;
    let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);

    // Adjust startPage if endPage reaches the limit early
    if (endPage === totalPages) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }

    const pages: number[] = [];
    for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
    }
    pagination.pageNumbers = pages;
};


const debouncedFetch = debounce(fetchCacheEntries, 400); // Debounce search input

watch(filters, () => {
    pagination.currentPage = 1; // Reset to page 1 on filter change
    debouncedFetch();
});

const changePage = (newPage: number) => {
  if (newPage >= 1 && newPage <= pagination.totalPages) {
    pagination.currentPage = newPage;
    fetchCacheEntries(); // Fetch immediately on page change
  }
};

const handleSizeChange = () => {
    pagination.currentPage = 1; // Reset to page 1
    fetchCacheEntries(); // Fetch immediately on size change
};

const formatDateTime = (isoString: string | null | undefined): string => {
  if (!isoString) return 'N/A';
  try {
    return new Date(isoString).toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  } catch { return 'Invalid Date'; }
};

const formatConfidence = (confidence: number | null | undefined): string => {
    if (confidence === null || confidence === undefined) return 'N/A';
    return `${(confidence * 100).toFixed(1)}%`;
};

const formatSource = (source: string | null | undefined): string => {
    if (!source) return 'Unknown';
    // Replace hyphens with spaces for better readability
    return source.replace(/-/g, ' ');
}

onMounted(() => {
  fetchCacheEntries();
});
</script>

<style scoped>
/* Add any component-specific styles here */
</style>
```

**3) Provide the COMPLETE UPDATED VERSION of any EXISTING files that need changes.**

```python
# <file path='app/core/initialize_db.py'>
# --- file path='app/core/initialize_db.py' ---
import logging
import time # Import time for retries
from sqlalchemy import create_engine, inspect as sql_inspect # Added inspect
from sqlalchemy.exc import SQLAlchemyError # Added for specific exception handling
from core.database import Base, SessionLocal, engine # Import engine directly
from core.config import settings
import sys
import uuid
from api.auth import get_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vendor_classification.db_init")

# Import all models to ensure they're registered with SQLAlchemy
logger.info("Importing models for database initialization")
try:
    from models.user import User
    from models.job import Job
    # --- ADDED: Import the new cache model ---
    from models.vendor_classification_cache import VendorClassificationCache
    # --- END ADDED ---
    # Import other models here if they exist
    logger.info("Models imported successfully.")
except ImportError as e:
    logger.critical(f"Failed to import models for DB initialization: {e}", exc_info=True)
    sys.exit(1) # Exit if models can't be imported

def create_or_update_admin_user():
    """
    Ensure the 'admin' user exists.
    If no user with username=admin, create one with default password 'password'.
    Otherwise, optionally update its password to ensure a consistent known credential.
    """
    db = None # Initialize db to None
    try:
        db = SessionLocal()
        logger.info("Checking for existing admin user...")
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            logger.info("Admin user already exists.")
            # OPTIONAL: Force-update the password each time:
            # If you do NOT want to re-hash or overwrite the password, remove below lines.
            try:
                logger.info("Attempting to update admin password to default 'password'...")
                admin_user.hashed_password = get_password_hash("password")
                db.commit()
                logger.info("Admin password was updated/reset to default: 'password'.")
            except Exception as hash_err:
                logger.error(f"Failed to update admin password: {hash_err}", exc_info=True)
                db.rollback() # Rollback password change on error
        else:
            logger.info("Admin user not found, creating default admin user...")
            admin_user = User(
                id=str(uuid.uuid4()),
                username="admin",
                email="admin@example.com",
                full_name="Admin User",
                hashed_password=get_password_hash("password"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("Created default admin user: admin / password")
    except SQLAlchemyError as e: # Catch specific DB errors
        logger.error(f"Database error during admin user check/creation: {e}", exc_info=True)
        if db: db.rollback()
    except Exception as e: # Catch other errors like hashing
        logger.error(f"Unexpected error ensuring admin user: {e}", exc_info=True)
        if db: db.rollback()
    finally:
        if db:
            db.close()
            logger.info("Admin user check/creation DB session closed.")

def initialize_database():
    """Initialize database by creating all tables, then ensuring 'admin' user exists."""
    max_retries = 5
    retry_delay = 5 # seconds
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting database initialization (Attempt {attempt + 1}/{max_retries})...")
            # Use the imported engine
            logger.info(f"Using database engine for URL: {settings.DATABASE_URL.split('@')[-1]}")

            # Check connection before creating tables
            with engine.connect() as connection:
                logger.info("Successfully connected to the database.")

            logger.info("Inspecting existing tables...")
            inspector = sql_inspect(engine)
            existing_tables = inspector.get_table_names()
            logger.info(f"Existing tables found: {existing_tables}")

            logger.info("Attempting to create all tables defined in Base.metadata...")
            # Log the tables Base knows about
            logger.info(f"Base.metadata knows about tables: {list(Base.metadata.tables.keys())}")
            Base.metadata.create_all(engine)
            logger.info("Base.metadata.create_all(engine) executed successfully.")

            # Verify tables were created
            logger.info("Re-inspecting tables after create_all...")
            inspector = sql_inspect(engine) # Re-inspect
            new_existing_tables = inspector.get_table_names()
            logger.info(f"Tables found after create_all: {new_existing_tables}")

            # Specifically check for 'users', 'jobs', and the new cache table
            expected_tables = ['users', 'jobs', 'vendor_classification_cache']
            for table_name in expected_tables:
                 if table_name not in new_existing_tables:
                     logger.error(f"'{table_name}' table NOT FOUND after create_all call!")
                 else:
                     logger.info(f"'{table_name}' table found after create_all call.")

            # Create or update the admin user
            create_or_update_admin_user()

            logger.info("Database initialization appears successful.")
            return True # Success

        except SQLAlchemyError as e:
            logger.error(f"Database connection or table creation error on attempt {attempt + 1}: {e}", exc_info=False) # Don't need full trace every retry
            if attempt + 1 == max_retries:
                logger.critical("Max retries reached. Database initialization failed.", exc_info=True)
                raise # Raise the last exception
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error during database initialization attempt {attempt + 1}: {e}", exc_info=True)
            # Decide if retry makes sense for unexpected errors, maybe not
            raise # Re-raise immediately for unexpected errors

    logger.error("Database initialization failed after all retries.")
    return False # Should not be reached if exceptions are raised

if __name__ == "__main__":
    logger.info("Starting database initialization script directly...")
    try:
        success = initialize_database()
        if success:
            logger.info("Database initialization script completed successfully.")
            sys.exit(0)
        else:
            logger.error("Database initialization script failed.")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Unhandled exception during database initialization script: {e}", exc_info=True)
        sys.exit(1)

```


```python
# <file path='app/tasks/classification_logic.py'>
import asyncio
import time
from datetime import datetime, timezone # Added timezone
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, select, update # For func.now(), select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert # For PostgreSQL UPSERT

from core.config import settings
from core.logging_config import get_logger
# Import context functions if needed directly (though often used via logger)
from core.log_context import set_log_context
# Import log helpers from utils
from utils.log_utils import LogTimer, log_function_call, log_duration

from models.job import Job, JobStatus, ProcessingStage
from models.taxonomy import Taxonomy
# --- ADDED: Import Cache Model ---
from models.vendor_classification_cache import VendorClassificationCache, CacheClassificationSource
# --- END ADDED ---
from services.llm_service import LLMService
from services.search_service import SearchService
# --- ADDED: Import normalization function for cache key consistency ---
from services.file_service import normalize_vendor_name_for_key
# --- END ADDED ---


logger = get_logger("vendor_classification.classification_logic")

# --- Constants ---
MAX_CONCURRENT_SEARCHES = 10 # Limit concurrent search/LLM processing for unknown vendors
BATCH_PROCESSING_TIMEOUT = 300.0 # Max time (seconds) per classification batch
SEARCH_CLASSIFY_TIMEOUT = 600.0 # Max time (seconds) per vendor search + recursive classification
CACHE_QUERY_BATCH_SIZE = 500 # How many vendors to query the cache for at once

# --- Helper Functions ---

def create_batches(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Create batches from a list of items."""
    if not items: return []
    if not isinstance(items, list):
        logger.warning(f"create_batches expected a list, got {type(items)}. Returning empty list.")
        return []
    if batch_size <= 0:
        logger.warning(f"Invalid batch_size {batch_size}, using default from settings.")
        batch_size = settings.BATCH_SIZE
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

def group_by_parent_category(
    results: Dict[str, Dict],
    parent_level: int,
    vendors_to_group_names: List[str]
) -> Dict[Optional[str], List[str]]:
    """
    Group a specific list of vendor names based on their classification result at the parent_level.
    Only includes vendors that were successfully classified with a valid ID at the parent level.
    Returns a dictionary mapping parent category ID to a list of vendor *names*.
    """
    grouped: Dict[Optional[str], List[str]] = {}
    parent_key = f"level{parent_level}"
    logger.debug(f"group_by_parent_category: Grouping {len(vendors_to_group_names)} vendors based on results from '{parent_key}'.")

    grouped_count = 0
    excluded_count = 0

    for vendor_name in vendors_to_group_names:
        # --- Use normalized name for lookup in results_dict ---
        normalized_name = normalize_vendor_name_for_key(vendor_name)
        vendor_results = results.get(normalized_name)
        # --- End Use normalized name ---
        level_result = None
        if vendor_results is not None:
            level_result = vendor_results.get(parent_key)
        else:
            logger.warning(f"group_by_parent_category: Vendor '{vendor_name}' (normalized: {normalized_name}) not found in results dictionary.")
            excluded_count += 1
            continue

        if level_result and isinstance(level_result, dict) and not level_result.get("classification_not_possible", True):
            category_id = level_result.get("category_id")
            if category_id and category_id not in ["N/A", "ERROR"]:
                if category_id not in grouped:
                    grouped[category_id] = []
                # --- Store original name in group, lookup was via normalized ---
                grouped[category_id].append(vendor_name)
                # --- End Store original name ---
                grouped_count += 1
                # Reduced verbosity: logger.debug(f"  Grouping vendor '{vendor_name}' under parent '{category_id}'.")
            else:
                logger.debug(f"  Excluding vendor '{vendor_name}': classified at '{parent_key}' but has invalid category_id '{category_id}'.")
                excluded_count += 1
        else:
            reason = "Not processed"
            if level_result and isinstance(level_result, dict):
                reason = level_result.get('classification_not_possible_reason', 'Marked not possible')
            elif not level_result:
                    reason = f"No result found for {parent_key}"
            logger.info(f"  Excluding vendor '{vendor_name}' from Level {parent_level + 1}: not successfully classified at '{parent_key}'. Reason: {reason}.")
            excluded_count += 1

    logger.info(f"group_by_parent_category: Finished grouping for Level {parent_level + 1}. Created {len(grouped)} groups, included {grouped_count} vendors, excluded {excluded_count} vendors.")
    return grouped

# --- Core Processing Logic ---

@log_function_call(logger, include_args=False) # Keep args=False
async def process_batch(
    batch_data: List[Dict[str, Any]], # Pass list of dicts including optional fields
    level: int,
    parent_category_id: Optional[str],
    taxonomy: Taxonomy,
    llm_service: LLMService,
    stats: Dict[str, Any],
    search_context: Optional[Dict[str, Any]] = None # ADDED: Optional search context
) -> Dict[str, Dict]:
    """
    Process a batch of vendors for a specific classification level (1-5), including taxonomy validation.
    Optionally uses search context for post-search classification attempts.
    Updates stats dictionary in place. Passes full vendor data and context to LLM.
    Returns results for the batch, keyed by **normalized** vendor name.
    """
    results = {} # Keyed by normalized vendor name
    if not batch_data:
        logger.warning(f"process_batch called with empty batch_data for Level {level}, Parent '{parent_category_id}'.")
        return results

    # --- Use normalized names for internal processing and result keys ---
    batch_normalized_names_map: Dict[str, str] = {
        normalize_vendor_name_for_key(vd.get('vendor_name', f'Unknown_{i}')): vd.get('vendor_name', f'Unknown_{i}')
        for i, vd in enumerate(batch_data)
    }
    batch_normalized_names = list(batch_normalized_names_map.keys())
    # --- End Use normalized names ---

    context_type = "Search Context" if search_context else "Initial Data"
    classification_source = "Search" if search_context else "Initial" # Determine source

    logger.info(f"process_batch: Starting Level {level} batch using {context_type}.",
                extra={"batch_size": len(batch_data), "parent_category_id": parent_category_id, "first_normalized_vendor": batch_normalized_names[0] if batch_normalized_names else 'N/A'})

    # --- Get valid category IDs for this level/parent (Updated for L5) ---
    valid_category_ids: Set[str] = set()
    category_id_lookup_error = False
    try:
        logger.debug(f"process_batch: Retrieving valid category IDs for Level {level}, Parent '{parent_category_id}'.")
        categories = []
        if level == 1:
            categories = taxonomy.get_level1_categories()
        elif parent_category_id:
            if level == 2: categories = taxonomy.get_level2_categories(parent_category_id)
            elif level == 3: categories = taxonomy.get_level3_categories(parent_category_id)
            elif level == 4: categories = taxonomy.get_level4_categories(parent_category_id)
            elif level == 5: categories = taxonomy.get_level5_categories(parent_category_id)
            else: logger.error(f"process_batch: Invalid level {level} requested."); categories = []
        else: logger.error(f"process_batch: Parent category ID is required for Level {level} but was not provided."); categories = []

        valid_category_ids = {cat.id for cat in categories}

        if not valid_category_ids:
            if level > 1 and parent_category_id: logger.warning(f"process_batch: No valid child categories found or retrieved for Level {level}, Parent '{parent_category_id}'. LLM cannot classify.")
            elif level == 1: logger.error("process_batch: No Level 1 categories found in taxonomy!"); category_id_lookup_error = True
        # else: logger.debug(f"process_batch: Found {len(valid_category_ids)} valid IDs for Level {level}, Parent '{parent_category_id}'. Example: {list(valid_category_ids)[:5]}") # Reduced verbosity

    except Exception as tax_err:
        logger.error(f"process_batch: Error getting valid categories from taxonomy", exc_info=True, extra={"level": level, "parent_category_id": parent_category_id})
        valid_category_ids = set(); category_id_lookup_error = True

    # --- Call LLM ---
    llm_response_data = None
    try:
        logger.info(f"process_batch: Calling LLM for Level {level}, Parent '{parent_category_id or 'None'}', Context: {context_type}")
        with LogTimer(logger, f"LLM classification - Level {level}, Parent '{parent_category_id or 'None'}' ({context_type})", include_in_stats=True):
            llm_response_data = await llm_service.classify_batch(
                batch_data=batch_data, level=level, taxonomy=taxonomy,
                parent_category_id=parent_category_id, search_context=search_context
            )
        logger.info(f"process_batch: LLM call completed for Level {level}, Parent '{parent_category_id or 'None'}'.")

        if llm_response_data and isinstance(llm_response_data.get("usage"), dict):
            usage = llm_response_data["usage"]
            stats["api_usage"]["openrouter_calls"] += 1
            stats["api_usage"]["openrouter_prompt_tokens"] += usage.get("prompt_tokens", 0)
            stats["api_usage"]["openrouter_completion_tokens"] += usage.get("completion_tokens", 0)
            stats["api_usage"]["openrouter_total_tokens"] += usage.get("total_tokens", 0)
        else: logger.warning("process_batch: LLM response missing or has invalid usage data.")

        if llm_response_data is None:
            logger.error("process_batch: Received None response from llm_service.classify_batch. Cannot process results.")
            raise ValueError("LLM service returned None, indicating a failure in the call.")

        llm_result = llm_response_data.get("result", {})
        classifications = llm_result.get("classifications", [])
        if not isinstance(classifications, list):
            logger.warning("LLM response 'classifications' is not a list.", extra={"response_preview": str(llm_result)[:500]})
            classifications = []

        logger.debug(f"process_batch: Received {len(classifications)} classifications from LLM for batch size {len(batch_data)} at Level {level}.")
        if llm_result.get("batch_id_mismatch"): logger.warning(f"process_batch: Processing batch despite batch_id mismatch warning from LLM service.")

        # --- Validate and process results ---
        processed_normalized_vendors_in_response = set()
        for classification in classifications:
            if not isinstance(classification, dict):
                logger.warning("Invalid classification item format received from LLM (not a dict)", extra={"item": classification})
                continue

            original_vendor_name = classification.get("vendor_name")
            if not original_vendor_name:
                logger.warning("Classification received without vendor_name", extra={"classification": classification})
                continue

            # --- Use normalized name as key ---
            normalized_vendor_name = normalize_vendor_name_for_key(original_vendor_name)
            processed_normalized_vendors_in_response.add(normalized_vendor_name)
            # --- End Use normalized name ---

            category_id = classification.get("category_id", "N/A")
            category_name = classification.get("category_name", "N/A")
            confidence = classification.get("confidence", 0.0)
            classification_not_possible = classification.get("classification_not_possible", False)
            reason = classification.get("classification_not_possible_reason")
            notes = classification.get("notes")
            is_valid_category = True

            # --- TAXONOMY VALIDATION ---
            if not classification_not_possible and not category_id_lookup_error and valid_category_ids:
                if category_id not in valid_category_ids:
                    is_valid_category = False
                    logger.warning(f"Invalid category ID '{category_id}' returned by LLM for vendor '{original_vendor_name}' (normalized: {normalized_vendor_name}) at level {level}, parent '{parent_category_id}'.",
                                    extra={"valid_ids_count": len(valid_category_ids)})
                    classification_not_possible = True
                    reason = f"Invalid category ID '{category_id}' returned by LLM (Valid examples: {list(valid_category_ids)[:3]})"
                    confidence = 0.0; category_id = "N/A"; category_name = "N/A"
                    stats["invalid_category_errors"] = stats.get("invalid_category_errors", 0) + 1
            elif not classification_not_possible and category_id_lookup_error: logger.warning(f"Cannot validate category ID '{category_id}' for '{original_vendor_name}' due to earlier taxonomy lookup error.")
            elif not classification_not_possible and not valid_category_ids and level > 1:
                logger.warning(f"Cannot validate category ID '{category_id}' for '{original_vendor_name}' because no valid child categories were found for parent '{parent_category_id}'.")
                is_valid_category = False; classification_not_possible = True
                reason = f"LLM returned category '{category_id}' but no valid children found for parent '{parent_category_id}'."; confidence = 0.0
                category_id = "N/A"; category_name = "N/A"
                stats["invalid_category_errors"] = stats.get("invalid_category_errors", 0) + 1
            # --- End TAXONOMY VALIDATION ---

            # --- Consistency Checks ---
            if classification_not_possible and confidence > 0.0:
                logger.warning("Correcting confidence to 0.0 for classification_not_possible=true", extra={"vendor": original_vendor_name})
                confidence = 0.0
            if not classification_not_possible and is_valid_category and (category_id == "N/A" or not category_id):
                logger.warning("Classification marked possible by LLM but category ID is 'N/A' or empty", extra={"vendor": original_vendor_name, "classification": classification})
                classification_not_possible = True; reason = reason or "Missing category ID despite LLM success claim"
                confidence = 0.0; category_id = "N/A"; category_name = "N/A"
            # --- End Consistency Checks ---

            # --- Store result keyed by normalized name ---
            results[normalized_vendor_name] = {
                "category_id": category_id,
                "category_name": category_name,
                "confidence": confidence,
                "classification_not_possible": classification_not_possible,
                "classification_not_possible_reason": reason,
                "notes": notes,
                "vendor_name": original_vendor_name, # Keep original name here
                "normalized_vendor_name": normalized_vendor_name, # Store normalized name too
                "classification_source": classification_source
            }
            # --- End Store result ---
            # logger.debug(f"process_batch: Processed result for '{original_vendor_name}' (normalized: {normalized_vendor_name}) at Level {level}. Possible: {not classification_not_possible}, ID: {category_id}") # Reduced verbosity

        # Handle missing vendors from batch (using normalized names)
        missing_normalized_vendors = set(batch_normalized_names) - processed_normalized_vendors_in_response
        if missing_normalized_vendors:
            logger.warning(f"LLM response did not include results for all vendors in the batch.", extra={"missing_normalized_vendors": list(missing_normalized_vendors), "level": level})
            for norm_name in missing_normalized_vendors:
                original_name = batch_normalized_names_map.get(norm_name, norm_name) # Get original name if possible
                results[norm_name] = {
                    "category_id": "N/A", "category_name": "N/A", "confidence": 0.0,
                    "classification_not_possible": True,
                    "classification_not_possible_reason": "Vendor missing from LLM response batch",
                    "notes": None,
                    "vendor_name": original_name,
                    "normalized_vendor_name": norm_name,
                    "classification_source": classification_source
                }

    except Exception as e:
        logger.error(f"Failed to process batch at Level {level} ({context_type})", exc_info=True,
                        extra={"batch_normalized_names": batch_normalized_names, "error": str(e)})
        # Mark all vendors in the batch as failed (using normalized names)
        for norm_name in batch_normalized_names:
            original_name = batch_normalized_names_map.get(norm_name, norm_name)
            results[norm_name] = {
                "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0,
                "classification_not_possible": True,
                "classification_not_possible_reason": f"Batch processing error: {str(e)[:100]}",
                "notes": None,
                "vendor_name": original_name,
                "normalized_vendor_name": norm_name,
                "classification_source": classification_source
            }
    logger.info(f"process_batch: Finished Level {level} batch for parent '{parent_category_id or 'None'}'. Returning {len(results)} results.")
    return results


@log_function_call(logger, include_args=False)
async def search_and_classify_recursively(
    vendor_data: Dict[str, Any], # Contains original vendor_name
    taxonomy: Taxonomy,
    llm_service: LLMService,
    search_service: SearchService,
    stats: Dict[str, Any],
    semaphore: asyncio.Semaphore,
    target_level: int # <<< ADDED target_level
) -> Dict[str, Any]:
    """
    Performs Tavily search, attempts L1 classification, and then recursively
    attempts L2 up to target_level classification using the search context.
    Controlled by semaphore.
    Returns the search_result_data dictionary, potentially augmented with
    classification results (keyed as classification_l1, classification_l2, etc.).
    Classification results within this dict will have `classification_source` set to 'Search'.
    The main keys in this dictionary will be **normalized** vendor names.
    """
    original_vendor_name = vendor_data.get('vendor_name', 'UnknownVendor')
    # --- Use normalized name ---
    normalized_vendor_name = normalize_vendor_name_for_key(original_vendor_name)
    # --- End Use normalized name ---

    logger.debug(f"search_and_classify_recursively: Waiting to acquire semaphore for vendor '{original_vendor_name}' (normalized: {normalized_vendor_name}).")
    async with semaphore: # Limit concurrency
        logger.info(f"search_and_classify_recursively: Acquired semaphore. Starting for vendor '{original_vendor_name}' (normalized: {normalized_vendor_name}) up to Level {target_level}.")
        search_result_data = {
            "vendor_name": original_vendor_name, # Keep original name for context
            "normalized_vendor_name": normalized_vendor_name, # Add normalized name
            "search_query": f"{original_vendor_name} company business type industry",
            "sources": [],
            "summary": None,
            "error": None,
            # Keys for storing classification results obtained via search
            "classification_l1": None, "classification_l2": None, "classification_l3": None,
            "classification_l4": None, "classification_l5": None
            }

        # --- 1. Perform Tavily Search ---
        try:
            logger.debug(f"search_and_classify_recursively: Calling search_service.search_vendor for '{original_vendor_name}'.")
            with LogTimer(logger, f"Tavily search for '{original_vendor_name}'", include_in_stats=True):
                tavily_response = await search_service.search_vendor(original_vendor_name)
            logger.debug(f"search_and_classify_recursively: search_service.search_vendor returned for '{original_vendor_name}'.")

            stats["api_usage"]["tavily_search_calls"] += 1
            search_result_data.update(tavily_response) # Update with actual search results or error

            source_count = len(search_result_data.get("sources", []))
            if search_result_data.get("error"):
                logger.warning(f"search_and_classify_recursively: Search failed", extra={"vendor": original_vendor_name, "error": search_result_data["error"]})
                search_result_data["classification_l1"] = {
                        "classification_not_possible": True,
                        "classification_not_possible_reason": f"Search error: {str(search_result_data['error'])[:100]}",
                        "confidence": 0.0,
                        "vendor_name": original_vendor_name, # Include original name
                        "normalized_vendor_name": normalized_vendor_name, # Include normalized name
                        "notes": "Search Failed",
                        "classification_source": "Search" # Source is Search
                }
                logger.debug(f"search_and_classify_recursively: Releasing semaphore early due to search error for '{original_vendor_name}'.")
                return search_result_data # Stop if search failed
            else:
                logger.info(f"search_and_classify_recursively: Search completed", extra={"vendor": original_vendor_name, "source_count": source_count, "summary_present": bool(search_result_data.get('summary'))})

        except Exception as search_exc:
            logger.error(f"search_and_classify_recursively: Unexpected error during Tavily search for {original_vendor_name}", exc_info=True)
            search_result_data["error"] = f"Unexpected search error: {str(search_exc)}"
            search_result_data["classification_l1"] = {
                    "classification_not_possible": True,
                    "classification_not_possible_reason": f"Search task error: {str(search_exc)[:100]}",
                    "confidence": 0.0,
                    "vendor_name": original_vendor_name,
                    "normalized_vendor_name": normalized_vendor_name,
                    "notes": "Search Failed",
                    "classification_source": "Search"
                }
            logger.debug(f"search_and_classify_recursively: Releasing semaphore early due to search exception for '{original_vendor_name}'.")
            return search_result_data # Stop if search failed

        # --- 2. Attempt L1 Classification using Search Results ---
        search_content_available = search_result_data.get("sources") or search_result_data.get("summary")
        if not search_content_available:
            logger.warning(f"search_and_classify_recursively: No usable search results found for vendor, cannot classify", extra={"vendor": original_vendor_name})
            search_result_data["classification_l1"] = {
                    "classification_not_possible": True,
                    "classification_not_possible_reason": "No search results content found",
                    "confidence": 0.0,
                    "vendor_name": original_vendor_name,
                    "normalized_vendor_name": normalized_vendor_name,
                    "notes": "No Search Content",
                    "classification_source": "Search"
            }
            logger.debug(f"search_and_classify_recursively: Releasing semaphore early due to no search content for '{original_vendor_name}'.")
            return search_result_data # Stop if no content

        valid_l1_category_ids: Set[str] = set(taxonomy.categories.keys())
        llm_response_l1 = None
        try:
            logger.debug(f"search_and_classify_recursively: Calling llm_service.process_search_results (L1) for '{original_vendor_name}'.")
            with LogTimer(logger, f"LLM L1 classification from search for '{original_vendor_name}'", include_in_stats=True):
                # This specific function is designed only for L1 from search results
                llm_response_l1 = await llm_service.process_search_results(vendor_data, search_result_data, taxonomy)
            logger.debug(f"search_and_classify_recursively: llm_service.process_search_results (L1) returned for '{original_vendor_name}'.")

            if llm_response_l1 is None:
                logger.error("search_and_classify_recursively: Received None response from llm_service.process_search_results. Cannot process L1.")
                raise ValueError("LLM service (process_search_results) returned None.")

            if isinstance(llm_response_l1.get("usage"), dict):
                usage = llm_response_l1["usage"]
                stats["api_usage"]["openrouter_calls"] += 1
                stats["api_usage"]["openrouter_prompt_tokens"] += usage.get("prompt_tokens", 0)
                stats["api_usage"]["openrouter_completion_tokens"] += usage.get("completion_tokens", 0)
                stats["api_usage"]["openrouter_total_tokens"] += usage.get("total_tokens", 0)

            l1_classification = llm_response_l1.get("result", {})
            # Ensure names and source are present
            l1_classification["vendor_name"] = original_vendor_name
            l1_classification["normalized_vendor_name"] = normalized_vendor_name
            l1_classification["classification_source"] = "Search"

            # Validate L1 result
            classification_not_possible_l1 = l1_classification.get("classification_not_possible", True)
            category_id_l1 = l1_classification.get("category_id", "N/A")
            is_valid_l1 = True

            if not classification_not_possible_l1 and valid_l1_category_ids:
                if category_id_l1 not in valid_l1_category_ids:
                    is_valid_l1 = False
                    logger.warning(f"Invalid L1 category ID '{category_id_l1}' from search LLM for '{original_vendor_name}'.", extra={"valid_ids_count": len(valid_l1_category_ids)})
                    l1_classification["classification_not_possible"] = True
                    l1_classification["classification_not_possible_reason"] = f"Invalid L1 category ID '{category_id_l1}' from search."
                    l1_classification["confidence"] = 0.0; l1_classification["category_id"] = "N/A"; l1_classification["category_name"] = "N/A"
                    stats["invalid_category_errors"] = stats.get("invalid_category_errors", 0) + 1

            if l1_classification.get("classification_not_possible") and l1_classification.get("confidence", 0.0) > 0.0: l1_classification["confidence"] = 0.0
            if not l1_classification.get("classification_not_possible") and not l1_classification.get("category_id", "N/A"):
                l1_classification["classification_not_possible"] = True; l1_classification["classification_not_possible_reason"] = "Missing L1 category ID despite LLM success claim"
                l1_classification["confidence"] = 0.0; l1_classification["category_id"] = "N/A"; l1_classification["category_name"] = "N/A"

            search_result_data["classification_l1"] = l1_classification # Store validated L1 result

        except Exception as llm_err:
            logger.error(f"search_and_classify_recursively: Error during LLM L1 processing for {original_vendor_name}", exc_info=True)
            search_result_data["error"] = search_result_data.get("error") or f"LLM L1 processing error: {str(llm_err)}"
            search_result_data["classification_l1"] = {
                "classification_not_possible": True, "classification_not_possible_reason": f"LLM L1 processing error: {str(llm_err)[:100]}",
                "confidence": 0.0, "vendor_name": original_vendor_name, "normalized_vendor_name": normalized_vendor_name,
                "notes": "LLM L1 Error", "classification_source": "Search"
            }
            logger.debug(f"search_and_classify_recursively: Releasing semaphore early due to L1 LLM exception for '{original_vendor_name}'.")
            return search_result_data # Stop if L1 classification failed

        # --- 3. Recursive Classification L2 up to target_level using Search Context ---
        current_parent_id = search_result_data["classification_l1"].get("category_id")
        classification_possible = not search_result_data["classification_l1"].get("classification_not_possible", True)

        if classification_possible and current_parent_id and current_parent_id != "N/A" and target_level > 1:
            logger.info(f"search_and_classify_recursively: L1 successful ({current_parent_id}), proceeding to L2-{target_level} for {original_vendor_name} using search context.")
            for level in range(2, target_level + 1):
                logger.debug(f"Attempting post-search Level {level} for {original_vendor_name}, parent {current_parent_id}")
                try:
                    logger.debug(f"search_and_classify_recursively: Calling process_batch (Level {level}) for '{original_vendor_name}' with search context.")
                    # Use process_batch for consistency in validation and structure
                    batch_result_dict = await process_batch(
                        batch_data=[vendor_data], # Batch of one (pass original data)
                        level=level,
                        parent_category_id=current_parent_id,
                        taxonomy=taxonomy,
                        llm_service=llm_service,
                        stats=stats,
                        search_context=search_result_data # Pass the full search results as context
                    )
                    logger.debug(f"search_and_classify_recursively: process_batch (Level {level}) returned for '{original_vendor_name}'.")

                    # --- Result is keyed by normalized name ---
                    level_result = batch_result_dict.get(normalized_vendor_name)
                    # --- End Result key ---
                    if level_result:
                        # Source is already set to 'Search' by process_batch when search_context is provided
                        search_result_data[f"classification_l{level}"] = level_result # Store result
                        if level_result.get("classification_not_possible", True):
                            logger.info(f"Post-search classification stopped at Level {level} for {original_vendor_name}. Reason: {level_result.get('classification_not_possible_reason')}")
                            break # Stop recursion if classification fails
                        else:
                            current_parent_id = level_result.get("category_id") # Update parent for next level
                            if not current_parent_id or current_parent_id == "N/A":
                                logger.warning(f"Post-search Level {level} successful but returned invalid parent_id '{current_parent_id}' for {original_vendor_name}. Stopping recursion.")
                                break
                    else:
                        logger.error(f"Post-search Level {level} batch processing did not return result for {original_vendor_name} (normalized: {normalized_vendor_name}). Stopping recursion.")
                        search_result_data[f"classification_l{level}"] = {
                                "classification_not_possible": True, "classification_not_possible_reason": f"Missing result from L{level} post-search batch",
                                "confidence": 0.0, "vendor_name": original_vendor_name, "normalized_vendor_name": normalized_vendor_name,
                                "notes": f"L{level} Error", "classification_source": "Search"
                        }
                        break

                except Exception as recursive_err:
                    logger.error(f"search_and_classify_recursively: Error during post-search Level {level} for {original_vendor_name}", exc_info=True)
                    search_result_data[f"classification_l{level}"] = {
                            "classification_not_possible": True, "classification_not_possible_reason": f"L{level} processing error: {str(recursive_err)[:100]}",
                            "confidence": 0.0, "vendor_name": original_vendor_name, "normalized_vendor_name": normalized_vendor_name,
                            "notes": f"L{level} Error", "classification_source": "Search"
                    }
                    break # Stop recursion on error
        else:
            logger.info(f"search_and_classify_recursively: L1 classification failed or not possible for {original_vendor_name}, or target level is 1. Skipping L2-{target_level}.")

        logger.info(f"search_and_classify_recursively: Finished for vendor", extra={"vendor": original_vendor_name, "normalized_vendor": normalized_vendor_name})
        logger.debug(f"search_and_classify_recursively: Releasing semaphore for vendor '{original_vendor_name}'.")
        return search_result_data


@log_function_call(logger, include_args=False) # Keep args=False
async def process_vendors(
    unique_vendors_map: Dict[str, Dict[str, Any]], # Map: normalized_name -> original_data_dict
    taxonomy: Taxonomy,
    results: Dict[str, Dict], # Main results dict, keyed by normalized_name
    stats: Dict[str, Any],
    job: Job,
    db: Session,
    llm_service: LLMService,
    search_service: SearchService,
    target_level: int # <<< ADDED target_level
):
    """
    Main orchestration function for processing vendors through the classification workflow (up to target_level),
    including recursive search for unknowns (up to target_level). Updates results and stats dictionaries in place.
    Uses normalized vendor names as keys internally and for cache lookups.
    """
    all_normalized_vendor_names = list(unique_vendors_map.keys()) # Get normalized names from map
    total_unique_vendors = len(all_normalized_vendor_names)
    processed_count = 0 # Count unique vendors processed in batches

    logger.info(f"Starting classification loop for {total_unique_vendors} unique vendors up to target Level {target_level}.")

    # --- ADDED: Cache Query Logic ---
    vendors_to_process_next_level_names = set(all_normalized_vendor_names) # Start with all unique normalized vendor names
    cached_vendors_found = 0
    cache_query_start_time = time.monotonic()

    logger.info(f"Querying classification cache for {len(vendors_to_process_next_level_names)} vendors...")
    # Query cache in batches
    cache_results_map: Dict[str, VendorClassificationCache] = {}
    name_batches = create_batches(list(vendors_to_process_next_level_names), CACHE_QUERY_BATCH_SIZE)
    for i, name_batch in enumerate(name_batches):
        logger.debug(f"Querying cache batch {i+1}/{len(name_batches)} (size: {len(name_batch)})")
        try:
            stmt = select(VendorClassificationCache).where(VendorClassificationCache.normalized_vendor_name.in_(name_batch))
            found_in_batch = db.execute(stmt).scalars().all()
            for cached_entry in found_in_batch:
                cache_results_map[cached_entry.normalized_vendor_name] = cached_entry
        except Exception as cache_err:
            logger.error(f"Error querying classification cache batch {i+1}", exc_info=True)
            # Continue processing without cache results for this batch

    if cache_results_map:
        logger.info(f"Found {len(cache_results_map)} vendors in the classification cache. Pre-populating results.")
        for normalized_name, cached_entry in cache_results_map.items():
            if normalized_name in vendors_to_process_next_level_names:
                cached_vendors_found += 1
                vendors_to_process_next_level_names.remove(normalized_name) # Remove from further processing

                # Reconstruct the results structure from cache data
                original_vendor_name = unique_vendors_map.get(normalized_name, {}).get('vendor_name', normalized_name) # Get original name
                results[normalized_name] = {
                    "vendor_name": original_vendor_name, # Store original name
                    "normalized_vendor_name": normalized_name,
                    "classification_source": "Cache", # Mark source as Cache
                    "cached_at": cached_entry.last_updated_at.isoformat(), # Add timestamp when cached
                    "cache_source_origin": cached_entry.classification_source.value, # Add original source from cache
                }
                for lvl in range(1, 6): # Populate all levels from cache
                    level_id = getattr(cached_entry, f"level{lvl}_id", None)
                    level_name = getattr(cached_entry, f"level{lvl}_name", None)
                    if level_id:
                         # For cached items, assume classification was possible up to achieved level
                         classification_possible = lvl <= cached_entry.target_level_achieved
                         results[normalized_name][f"level{lvl}"] = {
                             "category_id": level_id,
                             "category_name": level_name,
                             "confidence": cached_entry.final_confidence if lvl == cached_entry.target_level_achieved else None, # Confidence only at final level
                             "classification_not_possible": not classification_possible,
                             "classification_not_possible_reason": None if classification_possible else "From Cache (Below Target)",
                             "notes": f"Retrieved from cache (Origin: {cached_entry.classification_source.value})",
                             "vendor_name": original_vendor_name,
                             "normalized_vendor_name": normalized_name,
                             "classification_source": "Cache" # Mark level source as Cache
                         }
                    else:
                         # If a level is missing in cache, mark it as not possible
                         results[normalized_name][f"level{lvl}"] = {
                             "category_id": "N/A", "category_name": "N/A", "confidence": 0.0,
                             "classification_not_possible": True,
                             "classification_not_possible_reason": "Not present in cache",
                             "notes": f"Retrieved from cache (Origin: {cached_entry.classification_source.value})",
                             "vendor_name": original_vendor_name,
                             "normalized_vendor_name": normalized_name,
                             "classification_source": "Cache"
                         }

        logger.info(f"Resolved {cached_vendors_found} vendors from cache. {len(vendors_to_process_next_level_names)} vendors remaining for standard processing.")
    else:
        logger.info("No vendors found in the classification cache.")

    stats["cache_hits"] = cached_vendors_found
    stats["cache_query_duration_seconds"] = round(time.monotonic() - cache_query_start_time, 2)
    # --- END ADDED: Cache Query Logic ---


    # --- Initial Hierarchical Classification (Levels 1 to target_level) ---
    # vendors_to_process_next_level_names now contains only non-cached vendors
    initial_l4_success_count = 0 # Track L4 for stats
    initial_l5_success_count = 0 # Track L5 for stats

    for level in range(1, target_level + 1):
        if not vendors_to_process_next_level_names:
            logger.info(f"No non-cached vendors remaining to process for Level {level}. Skipping.")
            continue # Skip level if no vendors need processing

        # --- Get original names for this level's processing ---
        current_vendors_for_this_level_normalized = list(vendors_to_process_next_level_names)
        current_vendors_for_this_level_original = [
            unique_vendors_map[norm_name]['vendor_name'] for norm_name in current_vendors_for_this_level_normalized
            if norm_name in unique_vendors_map and 'vendor_name' in unique_vendors_map[norm_name]
        ]
        if len(current_vendors_for_this_level_original) != len(current_vendors_for_this_level_normalized):
             logger.warning(f"Mismatch between normalized and original vendor name counts for Level {level}")
        # --- End Get original names ---

        vendors_successfully_classified_in_level_normalized_names = set() # Track normalized names that pass this level

        stage_enum_name = f"CLASSIFICATION_L{level}"
        job.current_stage = getattr(ProcessingStage, stage_enum_name, ProcessingStage.PROCESSING).value

        # Adjust progress calculation based on target_level (distribute 0.7 across target_level steps)
        progress_per_level = 0.7 / target_level if target_level > 0 else 0.7
        # --- Base progress calculation on total unique vendors, not just remaining ---
        processed_so_far = total_unique_vendors - len(vendors_to_process_next_level_names)
        base_progress = 0.1 + (processed_so_far / total_unique_vendors * 0.7) if total_unique_vendors > 0 else 0.1
        job.progress = min(0.8, base_progress + ((level - 1) * progress_per_level))
        # --- End Base progress calculation ---

        logger.info(f"[process_vendors] Committing status update before Level {level}: {job.status}, {job.current_stage}, {job.progress:.3f}")
        try: db.commit()
        except Exception: logger.error("Failed to commit status update before level processing", exc_info=True); db.rollback()

        logger.info(f"===== Starting Initial Level {level} Classification =====",
                    extra={ "vendors_to_process": len(current_vendors_for_this_level_original), "progress": job.progress })

        if level == 1:
            # Pass original names to group_by_parent_category if level > 1
            grouped_vendors_original_names = { None: current_vendors_for_this_level_original }
            logger.info(f"Level 1: Processing all {len(current_vendors_for_this_level_original)} non-cached vendors.")
        else:
            logger.info(f"Level {level}: Grouping {len(current_vendors_for_this_level_original)} vendors based on Level {level-1} results.")
            # --- Group using original names, results dict uses normalized keys ---
            grouped_vendors_original_names = group_by_parent_category(results, level - 1, current_vendors_for_this_level_original)
            # --- End Group using original names ---
            logger.info(f"Level {level}: Created {len(grouped_vendors_original_names)} groups for processing.")

        processed_in_level_count = 0
        batch_counter_for_level = 0
        total_batches_for_level = sum( (len(names) + settings.BATCH_SIZE - 1) // settings.BATCH_SIZE for names in grouped_vendors_original_names.values() )
        logger.info(f"Level {level}: Total batches to process: {total_batches_for_level}")

        for parent_category_id, group_vendor_original_names in grouped_vendors_original_names.items():
            if not group_vendor_original_names:
                logger.debug(f"Skipping empty group for parent '{parent_category_id}' at Level {level}.")
                continue

            logger.info(f"Processing Level {level} group",
                        extra={"parent_category_id": parent_category_id, "vendor_count": len(group_vendor_original_names)})

            # --- Get full data dicts using original names to look up normalized keys ---
            group_vendor_data = []
            for orig_name in group_vendor_original_names:
                norm_name = normalize_vendor_name_for_key(orig_name)
                if norm_name in unique_vendors_map:
                    group_vendor_data.append(unique_vendors_map[norm_name])
                else:
                    logger.warning(f"Could not find data for original name '{orig_name}' (normalized: '{norm_name}') in unique_vendors_map for Level {level} batch.")
            # --- End Get full data dicts ---

            level_batches_data = create_batches(group_vendor_data, batch_size=settings.BATCH_SIZE)
            logger.debug(f"Created {len(level_batches_data)} batches for group '{parent_category_id}' at Level {level}.")

            for i, batch_data in enumerate(level_batches_data):
                batch_counter_for_level += 1
                # --- Log original names ---
                batch_original_names = [vd['vendor_name'] for vd in batch_data]
                # --- End Log original names ---
                logger.info(f"Processing Level {level} batch {i+1}/{len(level_batches_data)} for parent '{parent_category_id or 'None'}'",
                            extra={"batch_size": len(batch_data), "first_vendor": batch_original_names[0] if batch_original_names else 'N/A', "batch_num": batch_counter_for_level, "total_batches": total_batches_for_level})
                try:
                    logger.debug(f"Calling process_batch with timeout {BATCH_PROCESSING_TIMEOUT}s")
                    # --- process_batch returns results keyed by normalized name ---
                    batch_results = await asyncio.wait_for(
                        process_batch(batch_data, level, parent_category_id, taxonomy, llm_service, stats, search_context=None),
                        timeout=BATCH_PROCESSING_TIMEOUT
                    )
                    # --- End process_batch return ---
                    logger.debug(f"Level {level} batch {i+1} results received. Count: {len(batch_results)}.")

                    # --- Iterate using normalized names from batch_results ---
                    for normalized_name, classification in batch_results.items():
                        if normalized_name in results:
                            # Source is set to 'Initial' by process_batch when no search_context
                            results[normalized_name][f"level{level}"] = classification
                            processed_in_level_count += 1

                            if not classification.get("classification_not_possible", True):
                                vendors_successfully_classified_in_level_normalized_names.add(normalized_name)
                                # Update stats based on the actual level completed
                                if level == 4: initial_l4_success_count += 1
                                if level == 5: initial_l5_success_count += 1
                            # else: logger.debug(f"Vendor '{classification.get('vendor_name')}' not successfully classified at Level {level}. Reason: {classification.get('classification_not_possible_reason', 'Unknown')}. Will not proceed.") # Reduced verbosity
                        else:
                            logger.warning(f"Normalized vendor '{normalized_name}' from batch result not found in main results dictionary.", extra={"level": level})
                    # --- End Iterate using normalized names ---

                except asyncio.TimeoutError:
                    logger.error(f"Timeout processing Level {level} batch {i+1} for parent '{parent_category_id or 'None'}' after {BATCH_PROCESSING_TIMEOUT}s.",
                                 extra={"batch_vendors": batch_original_names})
                    # Mark all vendors in this batch as failed due to timeout (using normalized names)
                    for vendor_d in batch_data:
                        norm_name = normalize_vendor_name_for_key(vendor_d['vendor_name'])
                        if norm_name in results:
                            if f"level{level}" not in results[norm_name]:
                                results[norm_name][f"level{level}"] = {
                                    "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0,
                                    "classification_not_possible": True,
                                    "classification_not_possible_reason": f"Batch processing timed out after {BATCH_PROCESSING_TIMEOUT}s",
                                    "vendor_name": vendor_d['vendor_name'],
                                    "normalized_vendor_name": norm_name,
                                    "classification_source": "Initial"
                                }
                                processed_in_level_count += 1
                        else: logger.warning(f"Normalized vendor '{norm_name}' from timed-out batch not found in main results dictionary.", extra={"level": level})

                except Exception as batch_error:
                    logger.error(f"Error during initial batch processing logic (Level {level}, parent '{parent_category_id or 'None'}')", exc_info=True,
                                    extra={"batch_vendors": batch_original_names, "error": str(batch_error)})
                    # Mark all vendors in this batch as failed due to error (using normalized names)
                    for vendor_d in batch_data:
                        norm_name = normalize_vendor_name_for_key(vendor_d['vendor_name'])
                        if norm_name in results:
                            if f"level{level}" not in results[norm_name]:
                                results[norm_name][f"level{level}"] = {
                                    "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0,
                                    "classification_not_possible": True,
                                    "classification_not_possible_reason": f"Batch processing logic error: {str(batch_error)[:100]}",
                                    "vendor_name": vendor_d['vendor_name'],
                                    "normalized_vendor_name": norm_name,
                                    "classification_source": "Initial"
                                }
                                processed_in_level_count += 1
                        else: logger.warning(f"Normalized vendor '{norm_name}' from failed batch not found in main results dictionary.", extra={"level": level})


                # Update progress within the level (based on batches completed)
                level_progress_fraction = batch_counter_for_level / total_batches_for_level if total_batches_for_level > 0 else 1
                # --- Adjust progress update ---
                job.progress = min(0.8, base_progress + ((level - 1) * progress_per_level) + (progress_per_level * level_progress_fraction))
                # --- End Adjust progress update ---
                try: db.commit()
                except Exception: logger.error("Failed to commit progress update during batch processing", exc_info=True); db.rollback()

        logger.info(f"===== Initial Level {level} Classification Completed =====")
        logger.info(f"  Processed {processed_in_level_count} vendor results at Level {level}.")
        logger.info(f"  {len(vendors_successfully_classified_in_level_normalized_names)} non-cached vendors successfully classified and validated at Level {level}, proceeding to L{level+1}.")
        vendors_to_process_next_level_names = vendors_successfully_classified_in_level_normalized_names

    # --- End of Initial Level Loop ---
    logger.info(f"===== Finished Initial Hierarchical Classification Loop (Up to Level {target_level}) =====")

    # --- Identify vendors needing search (those not successfully classified at target_level, including cached ones below target) ---
    unknown_vendors_data_to_search = []
    # --- Iterate using all normalized names ---
    for normalized_name in all_normalized_vendor_names:
        is_classified_target = False
        classification_source = results.get(normalized_name, {}).get("classification_source", "Unknown")

        if normalized_name in results:
            target_level_result = results[normalized_name].get(f"level{target_level}")
            if target_level_result and isinstance(target_level_result, dict) and not target_level_result.get("classification_not_possible", True):
                if target_level_result.get("category_id") and target_level_result.get("category_id") not in ["N/A", "ERROR"]:
                    is_classified_target = True

        # Add to search if not classified OR if it came from cache but didn't reach the target level
        if not is_classified_target:
            original_vendor_name = unique_vendors_map.get(normalized_name, {}).get('vendor_name', normalized_name)
            if classification_source == "Cache":
                 # Check if cached level met or exceeded target
                 cached_achieved_level = results[normalized_name].get("level" + str(target_level), {}).get("classification_not_possible") is False
                 if not cached_achieved_level:
                     logger.debug(f"Vendor '{original_vendor_name}' (normalized: {normalized_name}) was cached but below target Level {target_level}. Adding to search list.")
                     if normalized_name in unique_vendors_map: unknown_vendors_data_to_search.append(unique_vendors_map[normalized_name])
                     else: logger.warning(f"Vendor '{normalized_name}' marked for search but not found in unique_vendors_map."); unknown_vendors_data_to_search.append({'vendor_name': original_vendor_name, 'normalized_vendor_name': normalized_name})
                 # else: logger.debug(f"Vendor '{normalized_name}' from cache met target level {target_level}. Skipping search.") # Reduced verbosity
            else: # Not from cache and not classified
                logger.debug(f"Vendor '{original_vendor_name}' (normalized: {normalized_name}) did not initially reach/pass target Level {target_level} classification. Adding to search list.")
                if normalized_name in unique_vendors_map: unknown_vendors_data_to_search.append(unique_vendors_map[normalized_name])
                else: logger.warning(f"Vendor '{normalized_name}' marked for search but not found in unique_vendors_map."); unknown_vendors_data_to_search.append({'vendor_name': original_vendor_name, 'normalized_vendor_name': normalized_name})
    # --- End Iterate using all normalized names ---


    stats["classification_not_possible_initial"] = len(unknown_vendors_data_to_search) # Renamed for clarity
    stats["successfully_classified_l4"] = initial_l4_success_count # Store initial L4 count (non-cached)
    stats["successfully_classified_l5"] = initial_l5_success_count # Store initial L5 count (non-cached)

    logger.info(f"Initial Classification Summary (Target L{target_level}): {total_unique_vendors - stats['classification_not_possible_initial']} reached target initially or via cache, {stats['classification_not_possible_initial']} require search.")
    if target_level >= 4: logger.info(f"  Ref: {initial_l4_success_count} reached L4 initially (non-cache).")
    if target_level >= 5: logger.info(f"  Ref: {initial_l5_success_count} reached L5 initially (non-cache).")

    # --- Search and Recursive Classification for Unknown Vendors (up to target_level) ---
    if unknown_vendors_data_to_search:
        job.current_stage = ProcessingStage.SEARCH.value
        job.progress = 0.8 # Progress after initial classification attempts
        logger.info(f"[process_vendors] Committing status update before Search stage: {job.status}, {job.current_stage}, {job.progress}")
        try: db.commit()
        except Exception: logger.error("Failed to commit status update before Search stage", exc_info=True); db.rollback()

        logger.info(f"===== Starting Search and Recursive Classification for {stats['classification_not_possible_initial']} Vendors (Up to Level {target_level}) =====")

        stats["search_attempts"] = len(unknown_vendors_data_to_search)

        search_tasks = []
        if MAX_CONCURRENT_SEARCHES <= 0:
            logger.error(f"MAX_CONCURRENT_SEARCHES is {MAX_CONCURRENT_SEARCHES}. Cannot proceed with search tasks.")
            raise ValueError("MAX_CONCURRENT_SEARCHES must be positive.")
        search_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SEARCHES)
        logger.info(f"Created search semaphore with concurrency limit: {MAX_CONCURRENT_SEARCHES}")

        for vendor_data in unknown_vendors_data_to_search:
            async def timed_search_classify_task(vd):
                vn = vd.get('vendor_name', 'UnknownVendor')
                norm_vn = normalize_vendor_name_for_key(vn)
                try:
                    logger.debug(f"Calling search_and_classify_recursively for '{vn}' (normalized: {norm_vn}) with timeout {SEARCH_CLASSIFY_TIMEOUT}s")
                    return await asyncio.wait_for(
                        search_and_classify_recursively(
                            vd, taxonomy, llm_service, search_service, stats, search_semaphore, target_level
                        ),
                        timeout=SEARCH_CLASSIFY_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Timeout (> {SEARCH_CLASSIFY_TIMEOUT}s) during search_and_classify_recursively for vendor: {vn} (normalized: {norm_vn})")
                    return {
                        "vendor_name": vn, "normalized_vendor_name": norm_vn, "search_query": f"{vn} company business type industry", "sources": [], "summary": None,
                        "error": f"Task timed out after {SEARCH_CLASSIFY_TIMEOUT} seconds.",
                        "classification_l1": {
                            "classification_not_possible": True, "classification_not_possible_reason": f"Search/classify task timed out (> {SEARCH_CLASSIFY_TIMEOUT}s)",
                            "confidence": 0.0, "vendor_name": vn, "normalized_vendor_name": norm_vn,
                            "notes": "Timeout", "classification_source": "Search"
                        },
                        "classification_l2": None, "classification_l3": None, "classification_l4": None, "classification_l5": None
                    }
                except Exception as task_exc:
                    logger.error(f"Exception during search_and_classify_recursively task for vendor {vn} (normalized: {norm_vn})", exc_info=task_exc)
                    return {
                         "vendor_name": vn, "normalized_vendor_name": norm_vn, "search_query": f"{vn} company business type industry", "sources": [], "summary": None,
                         "error": f"Task execution error: {str(task_exc)}",
                         "classification_l1": {
                             "classification_not_possible": True, "classification_not_possible_reason": f"Search/classify task error: {str(task_exc)[:100]}",
                             "confidence": 0.0, "vendor_name": vn, "normalized_vendor_name": norm_vn,
                             "notes": "Task Error", "classification_source": "Search"
                         },
                         "classification_l2": None, "classification_l3": None, "classification_l4": None, "classification_l5": None
                    }

            task = asyncio.create_task(timed_search_classify_task(vendor_data))
            search_tasks.append(task)

        logger.info(f"Gathering results for {len(search_tasks)} search & recursive classification tasks...")
        gather_start_time = time.monotonic()
        search_and_recursive_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        gather_duration = time.monotonic() - gather_start_time
        logger.info(f"Search & recursive classification tasks completed (asyncio.gather finished). Duration: {gather_duration:.3f}s")

        job.progress = 0.95 # Indicate search phase is done
        logger.info(f"[process_vendors] Committing progress update after search gather: {job.progress:.3f}")
        try: db.commit()
        except Exception: logger.error("Failed to commit progress update after search gather", exc_info=True); db.rollback()

        successful_l1_searches = 0
        successful_l5_searches = 0 # Track L5 success via search
        processed_search_count = 0

        logger.info(f"Processing {len(search_and_recursive_results)} results from search/recursive tasks.")
        for i, result_or_exc in enumerate(search_and_recursive_results):
            processed_search_count += 1
            if i >= len(unknown_vendors_data_to_search):
                logger.error(f"Search result index {i} out of bounds for unknown_vendors list.")
                continue

            # --- Get normalized name for lookup ---
            vendor_data = unknown_vendors_data_to_search[i]
            original_vendor_name = vendor_data.get('vendor_name', f'UnknownVendor_{i}')
            normalized_name = normalize_vendor_name_for_key(original_vendor_name)
            # --- End Get normalized name ---

            if normalized_name not in results:
                logger.warning(f"Vendor '{original_vendor_name}' (normalized: {normalized_name}) from search task not found in main results dict. Initializing.")
                results[normalized_name] = {"vendor_name": original_vendor_name, "normalized_vendor_name": normalized_name}

            results[normalized_name]["search_attempted"] = True # Add flag

            if isinstance(result_or_exc, Exception):
                logger.error(f"Error returned by asyncio.gather for vendor {original_vendor_name} (normalized: {normalized_name})", exc_info=result_or_exc)
                results[normalized_name]["search_results"] = {"error": f"Search task gather error: {str(result_or_exc)}"}
                logger.info(f"OVERWRITE_LOG: Search task gather failed for '{original_vendor_name}'. Marking L1 as failed.")
                results[normalized_name]["level1"] = {
                    "classification_not_possible": True, "classification_not_possible_reason": f"Search task gather error: {str(result_or_exc)[:100]}",
                    "confidence": 0.0, "vendor_name": original_vendor_name, "normalized_vendor_name": normalized_name,
                    "notes": "Search Gather Error", "classification_source": "Search"
                }
                for lvl in range(2, target_level + 1): results[normalized_name].pop(f"level{lvl}", None)

            elif isinstance(result_or_exc, dict):
                 search_data = result_or_exc
                 results[normalized_name]["search_results"] = search_data # Store raw search info

                 if search_data.get("error"):
                     logger.warning(f"Search/classify task for {original_vendor_name} failed or timed out. Error: {search_data['error']}")
                     l1_error_classification = search_data.get("classification_l1", {
                         "classification_not_possible": True, "classification_not_possible_reason": search_data['error'],
                         "confidence": 0.0, "vendor_name": original_vendor_name, "normalized_vendor_name": normalized_name,
                         "notes": "Task Failed/Timeout", "classification_source": "Search"
                     })
                     logger.info(f"OVERWRITE_LOG: Search task failed/timed out for '{original_vendor_name}'. Marking L1 as failed.")
                     results[normalized_name]["level1"] = l1_error_classification
                     for lvl in range(2, target_level + 1):
                         if f"level{lvl}" in results[normalized_name]:
                             logger.info(f"OVERWRITE_LOG: Clearing L{lvl} for '{original_vendor_name}' due to search task failure/timeout.")
                             results[normalized_name].pop(f"level{lvl}", None)
                 else:
                     l1_classification = search_data.get("classification_l1")
                     if l1_classification:
                         logger.info(f"OVERWRITE_LOG: Processing successful search results for '{original_vendor_name}'. Target Level: {target_level}.")
                         results[normalized_name]["classified_via_search"] = True
                         results[normalized_name]["classification_source"] = "Search" # Update overall source

                         logger.info(f"OVERWRITE_LOG: Overwriting L1 for '{original_vendor_name}' with search result. Possible: {not l1_classification.get('classification_not_possible', True)}")
                         results[normalized_name]["level1"] = l1_classification # Overwrite L1

                         if not l1_classification.get("classification_not_possible", True):
                             successful_l1_searches += 1
                             logger.debug(f"Vendor '{original_vendor_name}' successfully classified at L1 via search (ID: {l1_classification.get('category_id')}).")

                             for lvl in range(2, target_level + 1):
                                 search_lvl_key = f"classification_l{lvl}"
                                 main_lvl_key = f"level{lvl}"

                                 if search_lvl_key in search_data and search_data[search_lvl_key]:
                                     lvl_result_data = search_data[search_lvl_key]
                                     logger.info(f"OVERWRITE_LOG: Overwriting L{lvl} for '{original_vendor_name}' with search result. Possible: {not lvl_result_data.get('classification_not_possible', True)}")
                                     results[normalized_name][main_lvl_key] = lvl_result_data
                                     if lvl == 5 and not lvl_result_data.get("classification_not_possible", True):
                                         successful_l5_searches += 1
                                         logger.info(f"Vendor '{original_vendor_name}' reached L5 classification via search.")
                                 else:
                                     if main_lvl_key in results[normalized_name]:
                                         logger.info(f"OVERWRITE_LOG: Clearing L{lvl} for '{original_vendor_name}' as search path did not provide a result for this level.")
                                         results[normalized_name].pop(main_lvl_key, None)
                                     # else: logger.debug(f"OVERWRITE_LOG: No initial L{lvl} result to clear for '{original_vendor_name}' and no search result provided.") # Reduced verbosity

                         else: # L1 classification via search failed
                             reason = l1_classification.get("classification_not_possible_reason", "Search did not yield L1 classification")
                             logger.info(f"Vendor '{original_vendor_name}' could not be classified via search at L1. Reason: {reason}. Clearing higher levels.")
                             for lvl in range(2, target_level + 1):
                                 if f"level{lvl}" in results[normalized_name]:
                                     logger.info(f"OVERWRITE_LOG: Clearing L{lvl} for '{original_vendor_name}' due to L1 failure post-search.")
                                     results[normalized_name].pop(f"level{lvl}", None)
                     else:
                         logger.error(f"Search task for '{original_vendor_name}' returned dict but missing 'classification_l1'. Marking L1 as failed.")
                         results[normalized_name]["level1"] = { "classification_not_possible": True, "classification_not_possible_reason": "Internal search error (missing L1 result)", "confidence": 0.0, "vendor_name": original_vendor_name, "normalized_vendor_name": normalized_name, "notes": "Search Error", "classification_source": "Search"}
                         for lvl in range(2, target_level + 1): results[normalized_name].pop(f"level{lvl}", None)
            else: # Handle unexpected return type from gather
                logger.error(f"Unexpected result type for vendor {original_vendor_name} search task: {type(result_or_exc)}")
                results[normalized_name]["search_results"] = {"error": f"Unexpected search result type: {type(result_or_exc)}"}
                logger.info(f"OVERWRITE_LOG: Unexpected search result type for '{original_vendor_name}'. Marking L1 as failed.")
                results[normalized_name]["level1"] = { "classification_not_possible": True, "classification_not_possible_reason": "Internal search error (unexpected type)", "confidence": 0.0, "vendor_name": original_vendor_name, "normalized_vendor_name": normalized_name, "notes": "Search Error", "classification_source": "Search"}
                for lvl in range(2, target_level + 1):
                    if f"level{lvl}" in results[normalized_name]:
                        logger.info(f"OVERWRITE_LOG: Clearing L{lvl} for '{original_vendor_name}' due to unexpected search result type.")
                        results[normalized_name].pop(f"level{lvl}", None)


        stats["search_successful_classifications_l1"] = successful_l1_searches
        stats["search_successful_classifications_l5"] = successful_l5_searches

        # Recalculate final L5 success count based on the *final* state of results dict
        final_l5_success_count = 0
        if target_level >= 5:
            # --- Iterate using normalized names ---
            for normalized_name in all_normalized_vendor_names:
                l5_res = results.get(normalized_name, {}).get("level5")
                if l5_res and isinstance(l5_res, dict) and not l5_res.get("classification_not_possible", True):
                    final_l5_success_count += 1
            # --- End Iterate ---
            stats["successfully_classified_l5_total"] = final_l5_success_count # New stat key for clarity
            logger.info(f"Final recalculation: Total vendors successfully classified at L5: {stats['successfully_classified_l5_total']}")
        else:
            stats["successfully_classified_l5_total"] = 0

        logger.info(f"===== Unknown Vendor Search & Recursive Classification Completed =====")
        logger.info(f"  Attempted search for {stats['search_attempts']} vendors.")
        logger.info(f"  Successfully classified {successful_l1_searches} at L1 via search.")
        if target_level >= 5:
            logger.info(f"  Successfully classified {successful_l5_searches} at L5 via search path.")
            logger.info(f"  Total vendors successfully classified at L5 (final state): {stats['successfully_classified_l5_total']}")
    else:
        logger.info("No unknown vendors required search.")
        job.progress = 0.95 # Set progress high if search wasn't needed
        logger.info(f"[process_vendors] Committing status update as search was skipped: {job.progress:.3f}")
        try: db.commit()
        except Exception: logger.error("Failed to commit status update when skipping search", exc_info=True); db.rollback()

    logger.info("process_vendors function is returning.")


# --- ADDED: Function to populate cache ---
def populate_classification_cache(
    db: Session,
    job_id: str,
    job_type: JobType, # To determine source
    detailed_results: List[Dict[str, Any]], # Use the flattened results prepared for DB
    confidence_threshold: float = 0.95
):
    """
    Populates the VendorClassificationCache table with high-confidence results
    or results confirmed by review. Uses PostgreSQL ON CONFLICT DO UPDATE (UPSERT).

    Args:
        db: SQLAlchemy Session.
        job_id: The ID of the job generating these results.
        job_type: The type of the job (CLASSIFICATION or REVIEW).
        detailed_results: List of processed result dicts (matching JobResultItem schema).
        confidence_threshold: Minimum confidence score required for caching (unless from review).
    """
    cache_entries_to_upsert = []
    cache_source_map = {
        JobType.CLASSIFICATION: {
            "Initial": CacheClassificationSource.INITIAL_HIGH_CONFIDENCE,
            "Search": CacheClassificationSource.SEARCH_HIGH_CONFIDENCE,
            "Cache": None # Don't re-cache items that came from cache
        },
        JobType.REVIEW: {
            "Review": CacheClassificationSource.REVIEW_CONFIRMED,
            # Add others if review logic outputs different sources
        }
    }

    logger.info(f"Starting classification cache population for job {job_id} ({job_type.value}). Processing {len(detailed_results)} results.")
    eligible_count = 0

    for result in detailed_results:
        normalized_name = normalize_vendor_name_for_key(result.get("vendor_name", ""))
        if not normalized_name:
            logger.warning("Skipping cache population for result with missing or empty vendor name.")
            continue

        status = result.get("final_status")
        confidence = result.get("final_confidence")
        achieved_level = result.get("achieved_level", 0)
        result_source_str = result.get("classification_source", "Initial") # Source from the result item

        # Determine the CacheClassificationSource based on job type and result source
        cache_source: Optional[CacheClassificationSource] = None
        source_mapping = cache_source_map.get(job_type)
        if source_mapping:
            cache_source = source_mapping.get(result_source_str)

        # Conditions for caching:
        # 1. Status is 'Classified'
        # 2. Source is not 'Cache' (avoid re-caching)
        # 3. EITHER the job type is REVIEW (implying confirmation) OR confidence meets threshold
        # 4. A valid cache_source was determined
        should_cache = (
            status == "Classified" and
            result_source_str != "Cache" and
            cache_source is not None and
            (job_type == JobType.REVIEW or (confidence is not None and confidence >= confidence_threshold))
        )

        if should_cache:
            eligible_count += 1
            entry_data = {
                "normalized_vendor_name": normalized_name,
                "target_level_achieved": achieved_level,
                "level1_id": result.get("level1_id"),
                "level1_name": result.get("level1_name"),
                "level2_id": result.get("level2_id"),
                "level2_name": result.get("level2_name"),
                "level3_id": result.get("level3_id"),
                "level3_name": result.get("level3_name"),
                "level4_id": result.get("level4_id"),
                "level4_name": result.get("level4_name"),
                "level5_id": result.get("level5_id"),
                "level5_name": result.get("level5_name"),
                "final_confidence": confidence,
                "final_status": status, # Should be 'Classified'
                "classification_source": cache_source, # Use the mapped CacheClassificationSource
                "job_id_origin": job_id,
                # created_at is handled by server_default
                "last_updated_at": datetime.now(timezone.utc) # Set explicitly for UPSERT logic
            }
            cache_entries_to_upsert.append(entry_data)
        # else: # Reduced verbosity
            # logger.debug(f"Skipping cache for '{normalized_name}'. Conditions not met (Status: {status}, Source: {result_source_str}, Confidence: {confidence}, JobType: {job_type.value})")


    if not cache_entries_to_upsert:
        logger.info(f"No eligible entries found to upsert into the classification cache for job {job_id}.")
        return

    logger.info(f"Attempting to UPSERT {len(cache_entries_to_upsert)} entries into the classification cache for job {job_id}.")

    try:
        # Use PostgreSQL's ON CONFLICT DO UPDATE for UPSERT
        # Assumes PostgreSQL backend. Adapt for other databases if necessary.
        stmt = pg_insert(VendorClassificationCache).values(cache_entries_to_upsert)

        # Define what to update on conflict (when normalized_vendor_name already exists)
        # Update all fields except the primary key and created_at
        update_dict = {
            col.name: getattr(stmt.excluded, col.name)
            for col in VendorClassificationCache.__table__.columns
            if col.name not in ['normalized_vendor_name', 'created_at']
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=['normalized_vendor_name'], # The constraint column
            set_=update_dict
        )

        db.execute(stmt)
        db.commit()
        logger.info(f"Successfully upserted {len(cache_entries_to_upsert)} entries into the classification cache for job {job_id}.")
        stats["cache_entries_added_or_updated"] = len(cache_entries_to_upsert) # Add to stats

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during classification cache upsert for job {job_id}", exc_info=True, extra={"error_details": str(e)})
        stats["cache_population_errors"] = stats.get("cache_population_errors", 0) + 1
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during classification cache upsert for job {job_id}", exc_info=True)
        stats["cache_population_errors"] = stats.get("cache_population_errors", 0) + 1

# --- END ADDED ---

```

```python
# <file path='app/tasks/classification_tasks.py'>
# <file path='app/tasks/classification_tasks.py'>
# app/tasks/classification_tasks.py
import os
import asyncio
import logging
from datetime import datetime
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, List, Optional # <<< ADDED List, Optional

from core.database import SessionLocal
from core.config import settings
from core.logging_config import get_logger
# Import context functions from the new module
from core.log_context import set_correlation_id, set_job_id, set_log_context, clear_all_context
# Import log helpers from utils
from utils.log_utils import LogTimer, log_duration

from models.job import Job, JobStatus, ProcessingStage, JobType # <<< ADDED JobType
from services.file_service import read_vendor_file, normalize_vendor_data, generate_output_file, normalize_vendor_name_for_key # <<< ADDED normalize_vendor_name_for_key
from services.llm_service import LLMService
from services.search_service import SearchService
from utils.taxonomy_loader import load_taxonomy

# Import the refactored logic
# --- UPDATED: Import cache population function ---
from .classification_logic import process_vendors, populate_classification_cache
# --- END UPDATED ---
# Import the schema for type hinting
from schemas.job import JobResultItem
# Import review schemas/logic if needed (likely handled by separate task)
from schemas.review import ReviewResultItem


# Configure logger
logger = get_logger("vendor_classification.tasks")
# --- ADDED: Log confirmation ---
logger.debug("Successfully imported Dict and Any from typing for classification tasks.")
# --- END ADDED ---


# --- UPDATED: Helper function to process results for DB storage ---
def _prepare_detailed_results_for_storage(
    results_dict: Dict[str, Dict], # Keyed by normalized name
    target_level: int # Keep target_level for reference if needed, but we store all levels now
) -> List[Dict[str, Any]]:
    """
    Processes the complex results dictionary (containing level1, level2... sub-dicts, keyed by normalized name)
    into a flat list of dictionaries, where each dictionary represents a vendor
    and contains fields for all L1-L5 classifications, plus final status details.
    Matches the JobResultItem schema.
    THIS IS FOR **CLASSIFICATION** JOBS. Review jobs store results differently.
    """
    processed_list = []
    logger.info(f"Preparing detailed results for CLASSIFICATION job storage. Processing {len(results_dict)} vendors.")

    # --- Iterate using normalized name key ---
    for normalized_name, vendor_results in results_dict.items():
        # --- Get original name from the results if available ---
        original_vendor_name = vendor_results.get("vendor_name", normalized_name)
        # --- End Get original name ---

        # Initialize the flat structure for this vendor
        flat_result: Dict[str, Any] = {
            "vendor_name": original_vendor_name, # Use original name here
            "level1_id": None, "level1_name": None,
            "level2_id": None, "level2_name": None,
            "level3_id": None, "level3_name": None,
            "level4_id": None, "level4_name": None,
            "level5_id": None, "level5_name": None,
            "final_confidence": None,
            "final_status": "Not Possible", # Default status
            "classification_source": vendor_results.get("classification_source", "Initial"), # Get overall source
            "classification_notes_or_reason": None,
            "achieved_level": 0 # Default achieved level
        }

        deepest_successful_level = 0
        final_level_data = None
        final_source = vendor_results.get("classification_source", "Initial") # Use overall source as default
        final_notes_or_reason = None

        # Iterate through levels 1 to 5 to populate the flat structure
        for level in range(1, 6):
            level_key = f"level{level}"
            level_data = vendor_results.get(level_key)

            if level_data and isinstance(level_data, dict):
                flat_result[f"level{level}_id"] = level_data.get("category_id")
                flat_result[f"level{level}_name"] = level_data.get("category_name")

                if not level_data.get("classification_not_possible", True):
                    deepest_successful_level = level
                    final_level_data = level_data # Store data of the deepest successful level
                    # Use the source from the *specific level* if available
                    final_source = level_data.get("classification_source", final_source)
                    final_notes_or_reason = level_data.get("notes") # Get notes from successful level
                elif deepest_successful_level == 0 and level == 1: # Track L1 failure reason if nothing else succeeded
                    final_notes_or_reason = level_data.get("classification_not_possible_reason") or level_data.get("notes")
                    final_source = level_data.get("classification_source", final_source) # Use L1 source

        # Determine final status, confidence, and notes based on the deepest successful level
        if final_level_data:
            flat_result["final_status"] = "Classified"
            flat_result["final_confidence"] = final_level_data.get("confidence")
            flat_result["achieved_level"] = deepest_successful_level
            flat_result["classification_notes_or_reason"] = final_notes_or_reason
        else:
            flat_result["final_status"] = "Not Possible"
            flat_result["final_confidence"] = 0.0
            flat_result["achieved_level"] = 0
            # Use the reason/notes captured from L1 failure or search failure
            flat_result["classification_notes_or_reason"] = final_notes_or_reason

        # Set the final determined source
        flat_result["classification_source"] = final_source

        # Handle potential ERROR states explicitly (e.g., if L1 failed with ERROR)
        l1_data = vendor_results.get("level1")
        if l1_data and l1_data.get("category_id") == "ERROR":
            flat_result["final_status"] = "Error"
            flat_result["classification_notes_or_reason"] = l1_data.get("classification_not_possible_reason") or "Processing error occurred"
            final_source = l1_data.get("classification_source", "Initial") # Override source if error
            flat_result["classification_source"] = final_source


        # Validate against Pydantic model (optional, but good practice)
        try:
            JobResultItem.model_validate(flat_result)
            processed_list.append(flat_result)
        except Exception as validation_err:
            logger.error(f"Validation failed for prepared result of vendor '{original_vendor_name}' (normalized: {normalized_name})",
                         exc_info=True, extra={"result_data": flat_result})
            continue

    logger.info(f"Finished preparing {len(processed_list)} detailed result items for CLASSIFICATION job storage.")
    return processed_list
# --- END UPDATED ---


@shared_task(bind=True)
# --- UPDATED: Added target_level parameter ---
def process_vendor_file(self, job_id: str, file_path: str, target_level: int):
# --- END UPDATED ---
    """
    Celery task entry point for processing a vendor file (CLASSIFICATION job type).
    Orchestrates the overall process by calling the main async helper.

    Args:
        job_id: Job ID
        file_path: Path to vendor file
        target_level: The desired maximum classification level (1-5)
    """
    task_id = self.request.id if self.request and self.request.id else "UnknownTaskID"
    logger.info(f"***** process_vendor_file TASK RECEIVED (CLASSIFICATION) *****",
                extra={
                    "celery_task_id": task_id,
                    "job_id_arg": job_id,
                    "file_path_arg": file_path,
                    "target_level_arg": target_level # Log received target level
                })

    set_correlation_id(job_id) # Set correlation ID early
    set_job_id(job_id)
    set_log_context({"target_level": target_level, "job_type": JobType.CLASSIFICATION.value}) # Add target level and type to context
    logger.info(f"Starting vendor file processing task (inside function)",
                extra={"job_id": job_id, "file_path": file_path, "target_level": target_level})

    # Validate target_level
    if not 1 <= target_level <= 5:
        logger.error(f"Invalid target_level received: {target_level}. Must be between 1 and 5.")
        # Fail the job immediately if level is invalid
        db_fail = SessionLocal()
        try:
            job_fail = db_fail.query(Job).filter(Job.id == job_id).first()
            if job_fail:
                job_fail.fail(f"Invalid target level specified: {target_level}. Must be 1-5.")
                db_fail.commit()
        except Exception as db_err:
            logger.error("Failed to mark job as failed due to invalid target level", exc_info=db_err)
            db_fail.rollback()
        finally:
            db_fail.close()
        clear_all_context() # Clear context before returning
        return # Stop task execution

    # Initialize loop within the task context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger.debug(f"Created and set new asyncio event loop for job {job_id}")

    db = SessionLocal()
    job = None # Initialize job to None

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            # Verify the target level matches the job record (optional sanity check)
            if job.target_level != target_level:
                logger.warning(f"Task received target_level {target_level} but job record has {job.target_level}. Using task value: {target_level}.")
                # Optionally update job record here if desired, or just proceed with task value

            # Ensure job type is CLASSIFICATION
            if job.job_type != JobType.CLASSIFICATION.value:
                 logger.error(f"process_vendor_file task called for a non-CLASSIFICATION job.", extra={"job_id": job_id, "job_type": job.job_type})
                 raise ValueError(f"Job {job_id} is not a CLASSIFICATION job.")


            set_log_context({
                "company_name": job.company_name,
                "creator": job.created_by,
                "file_name": job.input_file_name
                # target_level and job_type already set above
            })
            logger.info(f"Processing file for company",
                        extra={"company": job.company_name})
        else:
            logger.error("Job not found in database at start of task!", extra={"job_id": job_id})
            loop.close() # Close loop if job not found
            db.close() # Close db session
            clear_all_context() # Clear context before returning
            return # Exit task if job doesn't exist

        logger.info(f"About to run async processing for job {job_id}")
        with LogTimer(logger, "Complete file processing", level=logging.INFO, include_in_stats=True):
            # Run the async function within the loop created for this task
            # --- UPDATED: Pass target_level to async helper ---
            loop.run_until_complete(_process_vendor_file_async(job_id, file_path, db, target_level))
            # --- END UPDATED ---

        logger.info(f"Vendor file processing completed successfully (async part finished)")

    except Exception as e:
        logger.error(f"Error processing vendor file task (in main try block)", exc_info=True, extra={"job_id": job_id})
        try:
            # Re-query the job within this exception handler if it wasn't fetched initially or became None
            db_error_session = SessionLocal()
            try:
                job_in_error = db_error_session.query(Job).filter(Job.id == job_id).first()
                if job_in_error:
                    if job_in_error.status != JobStatus.COMPLETED.value:
                        err_msg = f"Task failed: {type(e).__name__}: {str(e)}"
                        job_in_error.fail(err_msg[:2000]) # Limit error message length
                        db_error_session.commit()
                        logger.info(f"Job status updated to failed due to task error",
                                    extra={"error": str(e)})
                    else:
                        logger.warning(f"Task error occurred after job was marked completed, status not changed.",
                                        extra={"error": str(e)})
                else:
                    logger.error("Job not found when trying to mark as failed.", extra={"job_id": job_id})
            except Exception as db_error:
                logger.error(f"Error updating job status during task failure handling", exc_info=True,
                            extra={"original_error": str(e), "db_error": str(db_error)})
                db_error_session.rollback()
            finally:
                    db_error_session.close()
        except Exception as final_db_error:
                logger.critical(f"CRITICAL: Failed even to handle database update in task error handler.", exc_info=final_db_error)

    finally:
        if db: # Close the main session used by the async function
            db.close()
            logger.debug(f"Main database session closed for task.")
        if loop and not loop.is_closed():
            loop.close()
            logger.debug(f"Event loop closed for task.")
        clear_all_context()
        logger.info(f"***** process_vendor_file TASK FINISHED (CLASSIFICATION) *****", extra={"job_id": job_id})


# --- UPDATED: Added target_level parameter ---
async def _process_vendor_file_async(job_id: str, file_path: str, db: Session, target_level: int):
# --- END UPDATED ---
    """
    Asynchronous part of the vendor file processing (CLASSIFICATION job type).
    Sets up services, initializes stats, calls the core processing logic,
    handles final result generation, cache population, and job status updates.
    """
    logger.info(f"[_process_vendor_file_async] Starting async processing for job {job_id} to target level {target_level}")

    llm_service = LLMService()
    search_service = SearchService()

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.error(f"[_process_vendor_file_async] Job not found in database", extra={"job_id": job_id})
        return

    # --- Initialize stats (Updated for L5 and Cache) ---
    start_time = datetime.now()
    stats: Dict[str, Any] = {
        "job_id": job.id,
        "company_name": job.company_name,
        "target_level": target_level,
        "start_time": start_time.isoformat(),
        "end_time": None,
        "processing_duration_seconds": None,
        "total_vendors": 0,
        "unique_vendors": 0,
        "cache_hits": 0, # Added
        "cache_query_duration_seconds": 0.0, # Added
        "cache_entries_added_or_updated": 0, # Added
        "cache_population_errors": 0, # Added
        "successfully_classified_l4": 0,
        "successfully_classified_l5": 0,
        "successfully_classified_l5_total": 0, # Added for final count
        "classification_not_possible_initial": 0, # Renamed
        "invalid_category_errors": 0,
        "search_attempts": 0,
        "search_successful_classifications_l1": 0,
        "search_successful_classifications_l5": 0,
        "api_usage": {
            "openrouter_calls": 0, "openrouter_prompt_tokens": 0, "openrouter_completion_tokens": 0,
            "openrouter_total_tokens": 0, "tavily_search_calls": 0, "cost_estimate_usd": 0.0
        }
    }
    # --- End Initialize stats ---

    # --- Initialize results dictionary (keyed by normalized name) ---
    results_dict: Dict[str, Dict] = {}
    detailed_results_for_db: Optional[List[Dict[str, Any]]] = None
    # --- End Initialize results dictionary ---

    try:
        job.status = JobStatus.PROCESSING.value
        job.current_stage = ProcessingStage.INGESTION.value
        job.progress = 0.05
        logger.info(f"[_process_vendor_file_async] Committing initial status update: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"Job status updated", extra={"status": job.status, "stage": job.current_stage, "progress": job.progress})

        logger.info(f"Reading vendor file")
        with log_duration(logger, "Reading vendor file"): vendors_data = read_vendor_file(file_path)
        logger.info(f"Vendor file read successfully", extra={"vendor_count": len(vendors_data)})

        job.current_stage = ProcessingStage.NORMALIZATION.value
        job.progress = 0.1
        logger.info(f"[_process_vendor_file_async] Committing status update: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"Job status updated", extra={"stage": job.current_stage, "progress": job.progress})

        logger.info(f"Normalizing vendor data")
        with log_duration(logger, "Normalizing vendor data"): normalized_vendors_data = normalize_vendor_data(vendors_data)
        logger.info(f"Vendor data normalized", extra={"normalized_count": len(normalized_vendors_data)})

        logger.info(f"Identifying unique vendors (using normalized names)")
        # --- MODIFIED: Key unique map by normalized name ---
        unique_vendors_map: Dict[str, Dict[str, Any]] = {}
        for entry in normalized_vendors_data:
            original_name = entry.get('vendor_name')
            if original_name:
                normalized_name = normalize_vendor_name_for_key(original_name)
                if normalized_name and normalized_name not in unique_vendors_map:
                    entry['normalized_vendor_name'] = normalized_name # Store normalized name in the dict
                    unique_vendors_map[normalized_name] = entry
        # --- END MODIFIED ---
        logger.info(f"Unique vendors identified", extra={"unique_count": len(unique_vendors_map)})

        stats["total_vendors"] = len(normalized_vendors_data)
        stats["unique_vendors"] = len(unique_vendors_map)

        logger.info(f"Loading taxonomy")
        with log_duration(logger, "Loading taxonomy"): taxonomy = load_taxonomy()
        logger.info(f"Taxonomy loaded", extra={"taxonomy_version": taxonomy.version})

        # Initialize the results dict structure (keyed by normalized name)
        results_dict = {norm_name: {"vendor_name": data.get("vendor_name", norm_name), "normalized_vendor_name": norm_name}
                        for norm_name, data in unique_vendors_map.items()}

        logger.info(f"Starting vendor classification process by calling classification_logic.process_vendors up to Level {target_level}")
        # process_vendors will populate the results_dict in place (keyed by normalized name)
        await process_vendors(
            unique_vendors_map=unique_vendors_map, taxonomy=taxonomy, results=results_dict,
            stats=stats, job=job, db=db, llm_service=llm_service, search_service=search_service,
            target_level=target_level
        )
        logger.info(f"Vendor classification process completed (returned from classification_logic.process_vendors)")

        logger.info("Starting result generation phase.")

        job.current_stage = ProcessingStage.RESULT_GENERATION.value
        job.progress = 0.98 # Progress after all classification/search
        logger.info(f"[_process_vendor_file_async] Committing status update before result generation: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"Job status updated", extra={"stage": job.current_stage, "progress": job.progress})

        output_file_name = None # Initialize

        # --- Process results for DB Storage ---
        try:
            logger.info("Processing detailed results for database storage.")
            with log_duration(logger, "Processing detailed results"):
                 detailed_results_for_db = _prepare_detailed_results_for_storage(results_dict, target_level)
            logger.info(f"Processed {len(detailed_results_for_db)} items for detailed results storage.")
        except Exception as proc_err:
            logger.error("Failed during detailed results processing for DB", exc_info=True)
            detailed_results_for_db = None # Ensure it's None if processing failed
        # --- End Process results for DB Storage ---

        # --- Generate Excel File ---
        try:
                logger.info(f"Generating output file")
                with log_duration(logger, "Generating output file"):
                    # Pass the original *normalized* vendors data and the results_dict (keyed by normalized name)
                    output_file_name = generate_output_file(normalized_vendors_data, results_dict, job_id)
                logger.info(f"Output file generated", extra={"output_file": output_file_name})
        except Exception as gen_err:
                logger.error("Failed during output file generation", exc_info=True)
                job.fail(f"Failed to generate output file: {str(gen_err)}")
                db.commit()
                return # Stop processing
        # --- End Generate Excel File ---

        # --- Finalize stats ---
        end_time = datetime.now()
        processing_duration = (end_time - datetime.fromisoformat(stats["start_time"])).total_seconds()
        stats["end_time"] = end_time.isoformat()
        stats["processing_duration_seconds"] = round(processing_duration, 2)
        cost_input_per_1k = 0.0005; cost_output_per_1k = 0.0015
        estimated_cost = (stats["api_usage"]["openrouter_prompt_tokens"] / 1000) * cost_input_per_1k + \
                            (stats["api_usage"]["openrouter_completion_tokens"] / 1000) * cost_output_per_1k
        estimated_cost += (stats["api_usage"]["tavily_search_calls"] / 1000) * 4.0
        stats["api_usage"]["cost_estimate_usd"] = round(estimated_cost, 4)
        # --- End Finalize stats ---

        # --- ADDED: Populate Cache ---
        if detailed_results_for_db:
            logger.info("Populating classification cache...")
            with log_duration(logger, "Populating classification cache"):
                # Pass the prepared detailed results to the cache population function
                populate_classification_cache(
                    db=db,
                    job_id=job_id,
                    job_type=JobType.CLASSIFICATION, # This is a classification job
                    detailed_results=detailed_results_for_db,
                    confidence_threshold=settings.CACHE_CONFIDENCE_THRESHOLD # Use setting
                )
            logger.info("Classification cache population attempt finished.")
        else:
            logger.warning("Skipping cache population because detailed results preparation failed.")
        # --- END ADDED: Populate Cache ---

        # --- Final Commit Block ---
        try:
            logger.info("Attempting final job completion update in database.")
            job.complete(output_file_name, stats, detailed_results_for_db)
            job.progress = 1.0
            logger.info(f"[_process_vendor_file_async] Committing final job completion status.")
            db.commit()
            logger.info(f"Job completed successfully",
                        extra={
                            "processing_duration": processing_duration,
                            "output_file": output_file_name,
                            "target_level": target_level,
                            "detailed_results_stored": bool(detailed_results_for_db),
                            "detailed_results_count": len(detailed_results_for_db) if detailed_results_for_db else 0,
                            "cache_hits": stats.get("cache_hits", 0), # Log cache stats
                            "cache_entries_added_or_updated": stats.get("cache_entries_added_or_updated", 0), # Log cache stats
                            "openrouter_calls": stats["api_usage"]["openrouter_calls"],
                            "tokens_used": stats["api_usage"]["openrouter_total_tokens"],
                            "tavily_calls": stats["api_usage"]["tavily_search_calls"],
                            "estimated_cost": stats["api_usage"]["cost_estimate_usd"],
                            "invalid_category_errors": stats.get("invalid_category_errors", 0),
                            "successfully_classified_l5_total": stats.get("successfully_classified_l5_total", 0)
                        })
        except Exception as final_commit_err:
            logger.error("CRITICAL: Failed to commit final job completion status!", exc_info=True)
            db.rollback()
            try:
                db_fail_final = SessionLocal()
                job_fail_final = db_fail_final.query(Job).filter(Job.id == job_id).first()
                if job_fail_final:
                    err_msg = f"Failed during final commit: {type(final_commit_err).__name__}: {str(final_commit_err)}"
                    job_fail_final.fail(err_msg[:2000])
                    db_fail_final.commit()
                db_fail_final.close()
            except Exception as fail_err: logger.error("CRITICAL: Also failed to mark job as failed after final commit error.", exc_info=fail_err)
        # --- End Final Commit Block ---

    except (ValueError, FileNotFoundError, IOError) as file_err:
        logger.error(f"[_process_vendor_file_async] File reading or writing error", exc_info=True, extra={"error": str(file_err)})
        if job: job.fail(f"File processing error: {type(file_err).__name__}: {str(file_err)}"[:2000]); db.commit()
        else: logger.error("Job object was None during file error handling.")
    except SQLAlchemyError as db_err:
        logger.error(f"[_process_vendor_file_async] Database error during processing", exc_info=True, extra={"error": str(db_err)})
        db.rollback()
        if job:
            try:
                db_fail_db = SessionLocal()
                job_fail_db = db_fail_db.query(Job).filter(Job.id == job_id).first()
                if job_fail_db and job_fail_db.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                    job_fail_db.fail(f"Database error: {type(db_err).__name__}: {str(db_err)}"[:2000]); db_fail_db.commit()
                db_fail_db.close()
            except Exception as fail_err: logger.error("CRITICAL: Also failed to mark job as failed after database error.", exc_info=fail_err)
        else: logger.error("Job object was None during database error handling.")
    except Exception as async_err:
        logger.error(f"[_process_vendor_file_async] Unexpected error during async processing", exc_info=True, extra={"error": str(async_err)})
        db.rollback()
        if job:
            try:
                db_fail_unexpected = SessionLocal()
                job_fail_unexpected = db_fail_unexpected.query(Job).filter(Job.id == job_id).first()
                if job_fail_unexpected and job_fail_unexpected.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                    job_fail_unexpected.fail(f"Unexpected error: {type(async_err).__name__}: {str(async_err)}"[:2000]); db_fail_unexpected.commit()
                db_fail_unexpected.close()
            except Exception as fail_err: logger.error("CRITICAL: Also failed to mark job as failed after unexpected error.", exc_info=fail_err)
        else: logger.error("Job object was None during unexpected error handling.")
    finally:
        logger.info(f"[_process_vendor_file_async] Finished async processing for job {job_id}")


# --- ADDED: Reclassification Task ---
@shared_task(bind=True)
def reclassify_flagged_vendors_task(self, review_job_id: str):
    """
    Celery task entry point for re-classifying flagged vendors (REVIEW job type).
    Orchestrates the reclassification process.
    Includes cache population for confirmed results.
    """
    task_id = self.request.id if self.request and self.request.id else "UnknownTaskID"
    logger.info(f"***** reclassify_flagged_vendors_task TASK RECEIVED *****",
                extra={"celery_task_id": task_id, "review_job_id": review_job_id})

    set_correlation_id(review_job_id) # Use review job ID as correlation ID
    set_job_id(review_job_id)
    set_log_context({"job_type": JobType.REVIEW.value})
    logger.info(f"Starting reclassification task", extra={"review_job_id": review_job_id})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger.debug(f"Created and set new asyncio event loop for review job {review_job_id}")

    db = SessionLocal()
    review_job = None

    try:
        review_job = db.query(Job).filter(Job.id == review_job_id).first()
        if not review_job:
            logger.error("Review job not found in database at start of task!", extra={"review_job_id": review_job_id})
            raise ValueError("Review job not found.")

        if review_job.job_type != JobType.REVIEW.value:
            logger.error(f"reclassify_flagged_vendors_task called for a non-REVIEW job.", extra={"review_job_id": review_job_id, "job_type": review_job.job_type})
            raise ValueError(f"Job {review_job_id} is not a REVIEW job.")

        set_log_context({
            "company_name": review_job.company_name,
            "creator": review_job.created_by,
            "parent_job_id": review_job.parent_job_id
        })
        logger.info(f"Processing review for company", extra={"company": review_job.company_name})

        logger.info(f"About to run async reclassification processing for review job {review_job_id}")
        with LogTimer(logger, "Complete reclassification processing", level=logging.INFO, include_in_stats=True):
            loop.run_until_complete(_process_reclassification_async(review_job_id, db))

        logger.info(f"Reclassification processing completed successfully (async part finished)")

    except Exception as e:
        logger.error(f"Error processing reclassification task", exc_info=True, extra={"review_job_id": review_job_id})
        try:
            db_error_session = SessionLocal()
            try:
                job_in_error = db_error_session.query(Job).filter(Job.id == review_job_id).first()
                if job_in_error and job_in_error.status != JobStatus.COMPLETED.value:
                    job_in_error.fail(f"Reclassification task failed: {type(e).__name__}: {str(e)}"[:2000]); db_error_session.commit()
                    logger.info(f"Review job status updated to failed due to task error", extra={"error": str(e)})
                elif job_in_error: logger.warning(f"Task error occurred after review job was marked completed, status not changed.", extra={"error": str(e)})
                else: logger.error("Review job not found when trying to mark as failed.", extra={"review_job_id": review_job_id})
            except Exception as db_error: logger.error(f"Error updating review job status during task failure handling", exc_info=True, extra={"original_error": str(e), "db_error": str(db_error)}); db_error_session.rollback()
            finally: db_error_session.close()
        except Exception as final_db_error: logger.critical(f"CRITICAL: Failed even to handle database update in reclassification task error handler.", exc_info=final_db_error)

    finally:
        if db: db.close(); logger.debug(f"Main database session closed for reclassification task.")
        if loop and not loop.is_closed(): loop.close(); logger.debug(f"Event loop closed for reclassification task.")
        clear_all_context()
        logger.info(f"***** reclassify_flagged_vendors_task TASK FINISHED *****", extra={"review_job_id": review_job_id})


async def _process_reclassification_async(review_job_id: str, db: Session):
    """
    Asynchronous part of the reclassification task.
    Sets up services, calls the core reclassification logic, stores results,
    and populates the cache with confirmed results.
    """
    logger.info(f"[_process_reclassification_async] Starting async processing for review job {review_job_id}")

    llm_service = LLMService()
    review_job = db.query(Job).filter(Job.id == review_job_id).first()
    if not review_job:
        logger.error(f"[_process_reclassification_async] Review job not found in database", extra={"review_job_id": review_job_id})
        return

    from .reclassification_logic import process_reclassification # Import here

    # --- MODIFIED: Initialize final_stats ---
    review_results_list: Optional[List[Dict[str, Any]]] = None
    final_stats: Dict[str, Any] = { # Ensure stats dict exists
        "job_id": review_job.id,
        "company_name": review_job.company_name,
        "parent_job_id": review_job.parent_job_id,
        "job_type": JobType.REVIEW.value,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "processing_duration_seconds": None,
        "cache_entries_added_or_updated": 0, # Added
        "cache_population_errors": 0, # Added
        "api_usage": { "openrouter_calls": 0, "openrouter_prompt_tokens": 0, "openrouter_completion_tokens": 0, "openrouter_total_tokens": 0, "cost_estimate_usd": 0.0 }
    }
    # --- END MODIFIED ---

    try:
        review_job.status = JobStatus.PROCESSING.value
        review_job.current_stage = ProcessingStage.RECLASSIFICATION.value
        review_job.progress = 0.1
        logger.info(f"[_process_reclassification_async] Committing initial status update: {review_job.status}, {review_job.current_stage}, {review_job.progress}")
        db.commit()
        logger.info(f"Review job status updated", extra={"status": review_job.status, "stage": review_job.current_stage, "progress": review_job.progress})

        # --- Call the reclassification logic ---
        # Pass the stats dict to be updated
        review_results_list, temp_stats = await process_reclassification(
            review_job=review_job,
            db=db,
            llm_service=llm_service
        )
        final_stats.update(temp_stats) # Merge returned stats
        # --- End call ---

        logger.info(f"Reclassification logic completed. Processed {final_stats.get('total_items_processed', 0)} items.")
        review_job.progress = 0.95

        # --- ADDED: Populate Cache for REVIEW job ---
        if review_results_list:
            logger.info("Populating classification cache from REVIEW job results...")
            with log_duration(logger, "Populating classification cache (Review)"):
                populate_classification_cache(
                    db=db,
                    job_id=review_job_id,
                    job_type=JobType.REVIEW, # Mark as Review job
                    detailed_results=review_results_list, # Pass the results directly
                    # Confidence threshold is ignored for REVIEW jobs in populate_classification_cache
                )
            logger.info("Classification cache population attempt finished for REVIEW job.")
        else:
            logger.warning("Skipping cache population for REVIEW job because no results were generated.")
        # --- END ADDED: Populate Cache ---


        # --- Final Commit Block ---
        try:
            logger.info("Attempting final review job completion update in database.")
            # --- MODIFIED: Pass updated final_stats ---
            review_job.complete(output_file_name=None, stats=final_stats, detailed_results=review_results_list)
            # --- END MODIFIED ---
            review_job.progress = 1.0
            logger.info(f"[_process_reclassification_async] Committing final review job completion status.")
            db.commit()
            logger.info(f"Review job completed successfully",
                        extra={
                            "processing_duration": final_stats.get("processing_duration_seconds"),
                            "items_processed": final_stats.get("total_items_processed"),
                            "successful": final_stats.get("successful_reclassifications"),
                            "failed": final_stats.get("failed_reclassifications"),
                            "cache_added_updated": final_stats.get("cache_entries_added_or_updated", 0), # Log cache stat
                            "openrouter_calls": final_stats.get("api_usage", {}).get("openrouter_calls"),
                            "tokens_used": final_stats.get("api_usage", {}).get("openrouter_total_tokens"),
                            "estimated_cost": final_stats.get("api_usage", {}).get("cost_estimate_usd")
                        })
        except Exception as final_commit_err:
            logger.error("CRITICAL: Failed to commit final review job completion status!", exc_info=True)
            db.rollback()
            try:
                db_fail_final = SessionLocal()
                job_fail_final = db_fail_final.query(Job).filter(Job.id == review_job_id).first()
                if job_fail_final: job_fail_final.fail(f"Failed during final commit: {type(final_commit_err).__name__}: {str(final_commit_err)}"[:2000]); db_fail_final.commit()
                db_fail_final.close()
            except Exception as fail_err: logger.error("CRITICAL: Also failed to mark review job as failed after final commit error.", exc_info=fail_err)
        # --- End Final Commit Block ---

    except (ValueError, FileNotFoundError) as logic_err:
        logger.error(f"[_process_reclassification_async] Data or File error during reclassification logic", exc_info=True, extra={"error": str(logic_err)})
        if review_job: review_job.fail(f"Reclassification data error: {type(logic_err).__name__}: {str(logic_err)}"[:2000]); db.commit()
    except SQLAlchemyError as db_err:
         logger.error(f"[_process_reclassification_async] Database error during reclassification processing", exc_info=True, extra={"error": str(db_err)})
         db.rollback()
         try:
            db_fail_db = SessionLocal()
            job_fail_db = db_fail_db.query(Job).filter(Job.id == review_job_id).first()
            if job_fail_db and job_fail_db.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]: job_fail_db.fail(f"Database error: {type(db_err).__name__}: {str(db_err)}"[:2000]); db_fail_db.commit()
            db_fail_db.close()
         except Exception as fail_err: logger.error("CRITICAL: Also failed to mark review job as failed after database error.", exc_info=fail_err)

    except Exception as async_err:
        logger.error(f"[_process_reclassification_async] Unexpected error during async reclassification processing", exc_info=True, extra={"error": str(async_err)})
        db.rollback()
        try:
            db_fail_unexpected = SessionLocal()
            job_fail_unexpected = db_fail_unexpected.query(Job).filter(Job.id == review_job_id).first()
            if job_fail_unexpected and job_fail_unexpected.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]: job_fail_unexpected.fail(f"Unexpected error: {type(async_err).__name__}: {str(async_err)}"[:2000]); db_fail_unexpected.commit()
            db_fail_unexpected.close()
        except Exception as fail_err: logger.error("CRITICAL: Also failed to mark review job as failed after unexpected error.", exc_info=fail_err)
    finally:
        logger.info(f"[_process_reclassification_async] Finished async processing for review job {review_job_id}")

# --- END ADDED ---

```

```python
# <file path='app/api/main.py'>
# app/api/main.py
import socket
import sqlalchemy
import httpx
from fastapi import (
    FastAPI, Depends, HTTPException, UploadFile, File, Form,
    BackgroundTasks, status, Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse # Added FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel # Added for response model
from typing import Dict, Any, Optional, List
import uuid
import os
from datetime import datetime, timedelta, timezone # Added timezone
import logging
import time
from sqlalchemy.orm import Session

# --- Core Imports ---
# Import config module directly to access manual variables
from core import config
# Import settings object for other configurations
from core.config import settings
# Import logger and context functions from refactored modules
from core.logging_config import setup_logging, get_logger
from core.log_context import set_correlation_id, set_user, set_job_id, get_correlation_id
# Import middleware (which now uses updated context functions)
from middleware.logging_middleware import RequestLoggingMiddleware
from core.database import get_db, SessionLocal, engine
from core.initialize_db import initialize_database

# --- Model Imports ---
from models.job import Job, JobStatus, ProcessingStage
from models.user import User
# --- ADDED: Import cache model (needed for DB init check) ---
from models.vendor_classification_cache import VendorClassificationCache
# --- END ADDED ---

# --- Service Imports ---
from services.file_service import save_upload_file, validate_file_header

# --- Task Imports ---
from tasks.celery_app import celery_app
from tasks.classification_tasks import process_vendor_file

# --- Utility Imports ---
from utils.taxonomy_loader import load_taxonomy

# --- Auth Imports ---
from fastapi.security import OAuth2PasswordRequestForm
from api.auth import (
    get_current_user,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_active_superuser # Import superuser dependency
)

# --- Router Imports ---
from api import jobs as jobs_router
from api import users as users_router
from api import password_reset as password_reset_router
# --- ADDED: Import admin router ---
from api import admin as admin_router
# --- END ADDED ---

# --- Schema Imports ---
from schemas.job import JobResponse
from schemas.user import UserResponse as UserResponseSchema

# --- Logging Setup ---
# Initialize logging BEFORE creating the FastAPI app instance
setup_logging(log_level=logging.DEBUG, log_to_file=True, log_dir=settings.TAXONOMY_DATA_DIR.replace('taxonomy', 'logs'))
logger = get_logger("vendor_classification.api")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="NAICS Vendor Classification API",
    description="API for classifying vendors according to NAICS taxonomy",
    version="1.0.0",
)

# --- Middleware ---
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:8080", "http://127.0.0.1:8080", f"http://localhost:{settings.FRONTEND_URL.split(':')[-1]}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
logger.info("Including API routers...")
app.include_router(
    jobs_router.router,
    prefix="/api/v1/jobs",
    tags=["Jobs"],
    dependencies=[Depends(get_current_user)]
)
logger.info("Included jobs router with prefix /api/v1/jobs")

app.include_router(
    users_router.router,
    prefix="/api/v1/users",
    tags=["Users"],
)
logger.info("Included users router with prefix /api/v1/users")

app.include_router(
    password_reset_router.router,
    prefix="/api/v1/auth",
    tags=["Password Reset"],
)
logger.info("Included password reset router with prefix /api/v1/auth")

# --- ADDED: Include Admin Router ---
app.include_router(
    admin_router.router,
    prefix="/api/v1/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_active_superuser)] # Apply superuser dependency to all admin routes
)
logger.info("Included admin router with prefix /api/v1/admin")
# --- END ADDED ---

# --- End Include Routers ---

# --- Vue.js Frontend Serving Setup ---
VUE_BUILD_DIR = "/app/frontend/dist"
VUE_INDEX_FILE = os.path.join(VUE_BUILD_DIR, "index.html")
logger.info(f"Attempting to serve Vue frontend from: {VUE_BUILD_DIR}")
if not os.path.exists(VUE_BUILD_DIR):
    logger.error(f"Vue build directory NOT FOUND at {VUE_BUILD_DIR}. Frontend will not be served.")
elif not os.path.exists(VUE_INDEX_FILE):
    logger.error(f"Vue index.html NOT FOUND at {VUE_INDEX_FILE}. Frontend serving might fail.")
else:
    logger.info(f"Vue build directory and index.html found. Static files will be mounted.")

# --- API ROUTES ---

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    hostname = socket.gethostname()
    local_ip = ""
    try:
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
                local_ip = "Could not resolve IP"

    logger.info(f"Health check called", extra={"hostname": hostname, "ip": local_ip})
    db_status = "unknown"
    db = None
    try:
        db = SessionLocal()
        db.execute(sqlalchemy.text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health Check: Database connection error", exc_info=True, extra={"error_details": str(e)})
        db_status = f"error: {str(e)[:100]}"
    finally:
        if db:
            db.close()

    vue_frontend_status = "found" if os.path.exists(VUE_INDEX_FILE) else "missing"

    celery_broker_status = "unknown"
    celery_connection = None
    try:
        celery_connection = celery_app.connection(heartbeat=2.0)
        celery_connection.ensure_connection(max_retries=1, timeout=2)
        celery_broker_status = "connected"
    except Exception as celery_e:
        logger.error(f"Celery broker connection error during health check: {str(celery_e)}", exc_info=False)
        celery_broker_status = f"error: {str(celery_e)[:100]}"
    finally:
            if celery_connection:
                try: celery_connection.close()
                except Exception as close_err: logger.warning(f"Error closing celery connection in health check: {close_err}")

    # --- UPDATED: Use manually loaded config variables for API checks ---
    openrouter_status = "unknown"
    tavily_status = "unknown"
    tavily_api_functional = False # Added flag for Tavily functionality

    # Check OpenRouter configuration (using manually loaded keys)
    if config.MANUAL_OPENROUTER_PROVISIONING_KEYS and settings.OPENROUTER_API_BASE:
        openrouter_status = "CONFIGURED"
        if any("REPLACE_WITH_YOUR_VALID" in k for k in config.MANUAL_OPENROUTER_PROVISIONING_KEYS):
             openrouter_status = "CONFIGURED (PLACEHOLDER KEYS)"
             logger.warning("OpenRouter health check: Provisioning keys appear to be placeholders.")
    else:
        openrouter_status = "NOT CONFIGURED"
        logger.warning("OpenRouter provisioning keys or API base missing/empty for health check.")

    # Check Tavily configuration and functionality (using manually loaded keys)
    if config.MANUAL_TAVILY_API_KEYS:
        tavily_status = "CONFIGURED"
        if any("REPLACE_WITH_YOUR_VALID" in k for k in config.MANUAL_TAVILY_API_KEYS):
             tavily_status = "CONFIGURED (PLACEHOLDER KEYS)"
             logger.warning("Tavily health check: API keys appear to be placeholders.")
        else:
            # Try a real API call if keys seem valid
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    test_payload = {"api_key": config.MANUAL_TAVILY_API_KEYS[0], "query": "test", "max_results": 1}
                    response = await client.post("https://api.tavily.com/search", json=test_payload)
                    if response.status_code == 200:
                        tavily_api_functional = True
                        tavily_status = "API FUNCTIONAL" # More specific status
                    else:
                        logger.warning(f"Tavily health check API call failed with status {response.status_code}")
                        tavily_status = f"API ERROR ({response.status_code})"
            except Exception as e:
                logger.error(f"Tavily health check API call failed: {e}", exc_info=True)
                tavily_status = f"API ERROR ({type(e).__name__})"
    else:
        tavily_status = "NOT CONFIGURED"
        logger.warning("Tavily API keys missing/empty for health check.")
    # --- END UPDATED API CHECKS ---

    email_status = "configured" if settings.SMTP_HOST and settings.SMTP_USER and settings.EMAIL_FROM else "not_configured"

    return {
        "status": "healthy",
        "hostname": hostname,
        "ip": local_ip,
        "database": db_status,
        "celery_broker": celery_broker_status,
        "vue_frontend_index": vue_frontend_status,
        "email_service": email_status,
        "openrouter_status": openrouter_status, # Updated status name
        "tavily_status": tavily_status,         # Updated status name
        "tavily_api_functional": tavily_api_functional, # Added functional check result
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# --- Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    correlation_id = get_correlation_id() or str(uuid.uuid4())
    try: body_preview = str(await request.body())[:500]
    except Exception: body_preview = "[Could not read request body]"
    logger.error("Request validation failed (422)", extra={
        "error_details": exc.errors(), "request_body_preview": body_preview,
        "request_headers": dict(request.headers), "correlation_id": correlation_id,
        "path": request.url.path
    })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers={"X-Correlation-ID": correlation_id}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    correlation_id = get_correlation_id() or str(uuid.uuid4())
    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(log_level, f"HTTP Exception: {exc.status_code} - {exc.detail}", extra={
        "correlation_id": correlation_id,
        "request_headers": dict(request.headers),
        "path": request.url.path,
        "method": request.method,
        "status_code": exc.status_code,
        "detail": exc.detail,
    }, exc_info=(exc.status_code >= 500))

    headers = getattr(exc, "headers", {})
    headers["X-Correlation-ID"] = correlation_id

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    correlation_id = get_correlation_id() or str(uuid.uuid4())
    logger.error(f"Unhandled exception during request to {request.url.path}", exc_info=True, extra={
        "correlation_id": correlation_id, "request_headers": dict(request.headers),
        "path": request.url.path, "method": request.method,
    })
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred.", "correlation_id": correlation_id},
        headers={"X-Correlation-ID": correlation_id}
    )


# --- Authentication Endpoint ---
@app.post("/token", response_model=Dict[str, Any], tags=["Authentication"])
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Handles user login and returns JWT token and user details."""
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)
    client_host = request.client.host if request.client else "Unknown"
    logger.info(f"Login attempt", extra={"username": form_data.username, "ip": client_host})

    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Login failed: invalid credentials", extra={"username": form_data.username, "ip": client_host})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
                logger.warning(f"Login failed: user '{user.username}' is inactive.", extra={"ip": client_host})
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive user.",
                )

        set_user(user)
        access_token = create_access_token(subject=user.username)

        logger.info(f"Login successful, token generated", extra={ "username": user.username, "ip": client_host, "token_expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponseSchema.model_validate(user)
        }

    except HTTPException as http_exc:
        if http_exc.status_code not in [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST]:
                logger.error(f"Unexpected HTTP exception during login for {form_data.username}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected login error", exc_info=True, extra={"error": str(e), "username": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the login process."
        )

# --- File Validation Endpoint ---
class FileValidationResponse(BaseModel):
    is_valid: bool
    message: str
    detected_columns: List[str] = []
    missing_mandatory_columns: List[str] = []

@app.post("/api/v1/validate-upload", response_model=FileValidationResponse, status_code=status.HTTP_200_OK, tags=["File Operations"])
async def validate_uploaded_file_header(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Quickly validates the header of an uploaded Excel file.
    Checks for the mandatory 'vendor_name' column (case-insensitive).
    Returns validation status and detected columns.
    """
    set_user(current_user)
    validation_uuid = str(uuid.uuid4())[:8]

    log_extra = {
        "validation_id": validation_uuid,
        "uploaded_filename": file.filename,
        "username": current_user.username
    }
    logger.info("File validation request received", extra=log_extra)

    if not file.filename:
        logger.warning("Validation attempt with no filename.", extra=log_extra)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file type for validation: {file.filename}", extra=log_extra)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Please upload an Excel file (.xlsx or .xls).")

    try:
        validation_result = validate_file_header(file)

        log_safe_validation_result = {
            "validation_is_valid": validation_result.get("is_valid"),
            "validation_message": validation_result.get("message"),
            "validation_detected_columns": validation_result.get("detected_columns"),
            "validation_missing_columns": validation_result.get("missing_mandatory_columns")
        }
        current_log_extra = {**log_extra, **log_safe_validation_result}
        logger.info(f"File header validation completed", extra=current_log_extra)

        status_code = status.HTTP_200_OK
        if not validation_result["is_valid"]:
            pass # Stick with 200 OK, let frontend interpret is_valid

        return JSONResponse(
            status_code=status_code,
            content=validation_result
        )

    except ValueError as ve:
        logger.warning(f"Validation failed due to parsing error: {ve}", extra=log_extra)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error during file header validation", exc_info=True, extra=log_extra)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error validating file: {e}")
    finally:
        if hasattr(file, 'close') and callable(file.close):
            try:
                 file.close()
            except Exception:
                logger.warning("Error closing file stream after validation", extra=log_extra, exc_info=False)


# --- UPLOAD ROUTE ---
@app.post("/api/v1/upload", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED, tags=["File Operations"])
async def upload_vendor_file(
    background_tasks: BackgroundTasks,
    company_name: str = Form(...),
    target_level: int = Form(..., ge=1, le=5, description="Target classification level (1-5)"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts vendor file upload, creates a job, and queues it for processing.
    Allows specifying the target classification level.
    **Assumes frontend performs pre-validation using /validate-upload.**
    """
    job_id = str(uuid.uuid4())
    set_job_id(job_id)
    set_user(current_user)

    logger.info(f"Upload request received", extra={
        "job_id": job_id,
        "company_name": company_name,
        "target_level": target_level,
        "uploaded_filename": file.filename,
        "content_type": file.content_type,
        "username": current_user.username
    })

    if not file.filename:
        logger.warning("Upload attempt with no filename.", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file type uploaded: {file.filename}", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Please upload an Excel file (.xlsx or .xls).")

    saved_file_path = None
    try:
        logger.debug(f"Attempting to save uploaded file for job {job_id}")
        saved_file_path = save_upload_file(file=file, job_id=job_id)
        logger.info(f"File saved successfully for job {job_id}", extra={"saved_path": saved_file_path})
    except IOError as e:
        logger.error(f"Failed to save uploaded file for job {job_id}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during file upload/saving for job {job_id}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing upload: {e}")

    job = None
    try:
        logger.debug(f"Creating database job record for job {job_id}")
        job = Job(
            id=job_id,
            company_name=company_name,
            input_file_name=os.path.basename(saved_file_path),
            status=JobStatus.PENDING.value,
            current_stage=ProcessingStage.INGESTION.value,
            created_by=current_user.username,
            target_level=target_level
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info(f"Database job record created successfully for job {job_id}", extra={"target_level": job.target_level})
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create database job record for job {job_id}", exc_info=True)
        if saved_file_path and os.path.exists(saved_file_path):
            try: os.remove(saved_file_path)
            except OSError: logger.warning(f"Could not remove file {saved_file_path} after DB error.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create job record.")

    try:
        logger.info(f"Adding Celery task 'process_vendor_file' to background tasks for job {job_id}")
        background_tasks.add_task(process_vendor_file.delay, job_id=job_id, file_path=saved_file_path, target_level=target_level)
        logger.info(f"Celery task queued successfully for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to queue Celery task for job {job_id}", exc_info=True)
        if job:
            job.fail(f"Failed to queue processing task: {str(e)}")
            db.commit()
        else:
             logger.error(f"Job object was None when trying to mark as failed due to Celery queue error.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue job for processing.")

    logger.info(f"Upload request for job {job_id} processed successfully, returning 202 Accepted.")
    return JobResponse.model_validate(job)


# --- Mount Static Files (Vue App) ---
if os.path.exists(VUE_BUILD_DIR) and os.path.exists(VUE_INDEX_FILE):
    logger.info(f"Mounting Vue app from directory: {VUE_BUILD_DIR}")
    app.mount("/assets", StaticFiles(directory=os.path.join(VUE_BUILD_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_vue_app(request: Request, full_path: str):
        potential_file_path = os.path.join(VUE_BUILD_DIR, full_path.lstrip('/'))
        # --- UPDATED: Exclude /api paths more robustly ---
        if not full_path.startswith("api/") and not full_path.startswith("token"):
        # --- END UPDATED ---
            if os.path.isfile(potential_file_path) and os.path.basename(potential_file_path) != 'index.html':
                 logger.debug(f"Serving static file directly: {full_path}")
                 return FileResponse(potential_file_path)
            else:
                logger.debug(f"Serving index.html for SPA route or missing file: {full_path}")
                # Ensure index.html exists before serving
                if os.path.exists(VUE_INDEX_FILE):
                    return FileResponse(VUE_INDEX_FILE)
                else:
                    logger.error(f"Vue index.html NOT FOUND at {VUE_INDEX_FILE} when trying to serve SPA route.")
                    return JSONResponse(status_code=404, content={"detail": "Frontend entry point not found."})
        else:
            # This part should ideally not be reached if API routers are set up correctly
            logger.warning(f"Request for API path '{full_path}' reached fallback static file route. Returning 404.")
            return JSONResponse(status_code=404, content={"detail": "API route not found"})

else:
    logger.error(f"Cannot mount Vue app: Directory {VUE_BUILD_DIR} or index file {VUE_INDEX_FILE} not found.")
    @app.get("/", include_in_schema=False)
    async def missing_frontend():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"Frontend not found. Expected build files in {VUE_BUILD_DIR}"}
        )
# --- END VUE.JS FRONTEND SERVING SETUP ---

# --- Initialize Database on Startup ---
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: Initializing database...")
    try:
        initialize_database()
        logger.info("Database initialization check complete.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
# --- END Initialize Database ---

```

```typescript
// <file path='frontend/vue_frontend/src/services/api.ts'>
import axios, {
    type AxiosInstance,
    type InternalAxiosRequestConfig,
    type AxiosError // Import AxiosError type
} from 'axios';
import { useAuthStore } from '@/stores/auth'; // Adjust path as needed
// --- UPDATED: Import JobResultItem and ReviewResultItem ---
import type { JobDetails, JobResultItem, ReviewResultItem } from '@/stores/job'; // Adjust path as needed
// --- END UPDATED ---

// --- Define API Response Interfaces ---

// Matches backend schemas/user.py -> UserResponse
export interface UserResponse {
    email: string;
    full_name: string | null;
    is_active: boolean | null;
    is_superuser: boolean | null;
    username: string;
    id: string; // UUID as string
    created_at: string; // ISO Date string
    updated_at: string; // ISO Date string
}

// Matches backend schemas/user.py -> UserCreate (for request body)
export interface UserCreateData {
    email: string;
    full_name?: string | null;
    is_active?: boolean | null;
    is_superuser?: boolean | null;
    username: string;
    password?: string; // Password required on create
}

// Matches backend schemas/user.py -> UserUpdate (for request body)
export interface UserUpdateData {
    email?: string | null;
    full_name?: string | null;
    password?: string | null; // Optional password update
    is_active?: boolean | null;
    is_superuser?: boolean | null;
}


// Matches backend response for /token (modified to include user object)
interface AuthResponse {
    access_token: string;
    token_type: string;
    user: UserResponse; // Include the user details
}

// --- ADDED: File Validation Response Interface ---
// Matches backend api/main.py -> FileValidationResponse
export interface FileValidationResponse {
    is_valid: boolean;
    message: string;
    detected_columns: string[];
    missing_mandatory_columns: string[];
}
// --- END ADDED ---

// Matches backend response for /api/v1/jobs/{job_id}/notify
interface NotifyResponse {
    success: boolean;
    message: string;
}

// Matches backend response for /api/v1/jobs/ (list endpoint)
// Should align with app/schemas/job.py -> JobResponse
export interface JobResponse {
    id: string;
    company_name: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_stage: string;
    created_at: string; // ISO Date string
    updated_at?: string | null;
    completed_at?: string | null;
    output_file_name?: string | null;
    input_file_name: string;
    created_by: string;
    error_message?: string | null;
    target_level: number; // Ensure target_level is included here
    // --- ADDED: Job Type and Parent Link ---
    job_type: 'CLASSIFICATION' | 'REVIEW';
    parent_job_id: string | null;
    // --- END ADDED ---
}

// --- ADDED: Job Results Response Interface ---
// Matches backend schemas/job.py -> JobResultsResponse
export interface JobResultsResponse {
    job_id: string;
    job_type: 'CLASSIFICATION' | 'REVIEW';
    results: JobResultItem[] | ReviewResultItem[]; // Union type
}
// --- END ADDED ---


// Matches backend models/classification.py -> ProcessingStats and console log
export interface JobStatsData {
    job_id: string;
    company_name: string;
    start_time: string | null; // Assuming ISO string
    end_time: string | null; // Assuming ISO string
    processing_duration_seconds: number | null; // Renamed from processing_time
    total_vendors: number | null; // Added
    unique_vendors: number | null; // Added (was present in console)
    target_level: number | null; // Added target level to stats
    // --- ADDED: Cache Stats ---
    cache_hits?: number | null;
    cache_query_duration_seconds?: number | null;
    cache_entries_added_or_updated?: number | null;
    cache_population_errors?: number | null;
    // --- END ADDED ---
    successfully_classified_l4: number | null; // Keep for reference
    successfully_classified_l5: number | null; // Keep L5 count
    successfully_classified_l5_total?: number | null; // Added final total
    classification_not_possible_initial: number | null; // Added
    invalid_category_errors: number | null; // Added (was present in console)
    search_attempts: number | null; // Added
    search_successful_classifications_l1: number | null; // Added
    search_successful_classifications_l5: number | null; // Renamed from search_assisted_l5
    api_usage: { // Nested structure
        openrouter_calls: number | null;
        openrouter_prompt_tokens: number | null;
        openrouter_completion_tokens: number | null;
        openrouter_total_tokens: number | null;
        tavily_search_calls: number | null;
        cost_estimate_usd: number | null;
    } | null; // Allow api_usage itself to be null if not populated
    // --- ADDED: Stats specific to REVIEW jobs ---
    reclassify_input?: Array<{ vendor_name: string; hint: string }>; // Input hints
    total_items_processed?: number;
    successful_reclassifications?: number;
    failed_reclassifications?: number;
    parent_job_id?: string; // Include parent ID in stats for review jobs
    // --- END ADDED ---
}


// Structure for download result helper
interface DownloadResult {
    blob: Blob;
    filename: string;
}

// Parameters for the job history list endpoint
interface GetJobsParams {
    status?: string;
    start_date?: string; // ISO string format
    end_date?: string; // ISO string format
    job_type?: 'CLASSIFICATION' | 'REVIEW'; // Filter by type
    skip?: number;
    limit?: number;
}

// --- ADDED: Password Reset Interfaces ---
// Matches backend schemas/password_reset.py -> MessageResponse
interface MessageResponse {
    message: string;
}
// --- END ADDED ---

// --- ADDED: Reclassification Interfaces ---
// Matches backend schemas/review.py -> ReclassifyRequestItem
interface ReclassifyRequestItemData {
    vendor_name: string;
    hint: string;
}
// Matches backend schemas/review.py -> ReclassifyResponse
interface ReclassifyResponseData {
    review_job_id: string;
    message: string;
}
// --- END ADDED ---

// --- ADDED: Admin Cache Interfaces ---
// Matches backend models/vendor_classification_cache.py -> CacheClassificationSource
export type CacheClassificationSource =
    | "Initial-HighConfidence"
    | "Search-HighConfidence"
    | "Review-Confirmed"
    | "Admin-Manual";

// Matches backend schemas/admin.py -> VendorCacheItemResponse
export interface VendorCacheItem {
    normalized_vendor_name: string;
    target_level_achieved: number;
    level1_id: string | null;
    level1_name: string | null;
    level2_id: string | null;
    level2_name: string | null;
    level3_id: string | null;
    level3_name: string | null;
    level4_id: string | null;
    level4_name: string | null;
    level5_id: string | null;
    level5_name: string | null;
    final_confidence: number | null;
    final_status: string; // Should be 'Classified'
    classification_source: CacheClassificationSource;
    job_id_origin: string;
    created_at: string; // ISO Date string
    last_updated_at: string; // ISO Date string
}

// Matches backend schemas/admin.py -> PaginatedVendorCacheResponse
export interface PaginatedVendorCacheResponse {
    total: number;
    items: VendorCacheItem[];
    page: number;
    size: number;
    pages: number;
}

// Parameters for the admin cache list endpoint
interface GetCacheEntriesParams {
    search?: string;
    source?: CacheClassificationSource | ''; // Allow empty string for 'All'
    page?: number;
    size?: number;
}
// --- END ADDED ---


// --- Axios Instance Setup ---

const axiosInstance: AxiosInstance = axios.create({
    baseURL: '/api/v1', // Assumes Vite dev server proxies /api/v1 to your backend
    timeout: 60000, // 60 seconds timeout
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
});

// --- Request Interceptor (Add Auth Token) ---
axiosInstance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const authStore = useAuthStore();
        const token = authStore.getToken();
        // Define URLs that should NOT receive the auth token
        const noAuthUrls = ['/auth/password-recovery', '/auth/reset-password', '/users/register'];

        // Check if the request URL matches any of the no-auth URLs
        const requiresAuth = token && config.url && !noAuthUrls.some(url => config.url?.startsWith(url));

        if (requiresAuth) {
            // LOGGING: Log token presence and target URL
            // console.log(`[api.ts Request Interceptor] Adding token for URL: ${config.url}`);
            config.headers.Authorization = `Bearer ${token}`;
        } else {
            // console.log(`[api.ts Request Interceptor] No token added for URL: ${config.url} (Token: ${token ? 'present' : 'missing'}, No-Auth Match: ${!requiresAuth && !!token})`);
        }
        return config;
    },
    (error: AxiosError) => {
        console.error('[api.ts Request Interceptor] Error:', error);
        return Promise.reject(error);
    }
);

// --- Response Interceptor (Handle Errors) ---
axiosInstance.interceptors.response.use(
    (response) => {
        // LOGGING: Log successful response status and URL
        // console.log(`[api.ts Response Interceptor] Success for URL: ${response.config.url} | Status: ${response.status}`);
        return response;
    },
    (error: AxiosError) => {
        console.error('[api.ts Response Interceptor] Error:', error.config?.url, error.response?.status, error.message);
        const authStore = useAuthStore();

        if (error.response) {
            const { status, data } = error.response;

            // Handle 401 Unauthorized (except for login attempts and public auth operations)
            const isLoginAttempt = error.config?.url === '/token'; // Base URL for login
            const isPublicAuthOperation = error.config?.url?.startsWith('/auth/') || error.config?.url?.startsWith('/users/register');

            if (status === 401 && !isLoginAttempt && !isPublicAuthOperation) {
                console.warn('[api.ts Response Interceptor] Received 401 Unauthorized on protected route. Logging out.');
                authStore.logout(); // Trigger logout action
                return Promise.reject(new Error('Session expired. Please log in again.'));
            }

            // Extract detailed error message from response data
            let detailMessage = 'An error occurred.';
            const responseData = data as any;

            if (responseData?.detail && Array.isArray(responseData.detail)) {
                 detailMessage = `Validation Error: ${responseData.detail.map((err: any) => `${err.loc?.join('.') ?? 'field'}: ${err.msg}`).join('; ')}`;
            }
            else if (responseData?.detail && typeof responseData.detail === 'string') {
                detailMessage = responseData.detail;
            }
            else if (typeof data === 'string' && data.length > 0 && data.length < 300) {
                detailMessage = data;
            }
            else if (error.message) {
                detailMessage = error.message;
            }

            const errorMessage = status === 422 ? detailMessage : `Error ${status}: ${detailMessage}`;
            console.error(`[api.ts Response Interceptor] Rejecting with error: ${errorMessage}`); // LOGGING
            return Promise.reject(new Error(errorMessage));

        } else if (error.request) {
            console.error('[api.ts Response Interceptor] Network error or no response received:', error.request);
            return Promise.reject(new Error('Network error or server did not respond. Please check connection.'));
        } else {
            console.error('[api.ts Response Interceptor] Axios setup error:', error.message);
            return Promise.reject(new Error(`Request setup error: ${error.message}`));
        }
    }
);


// --- API Service Object ---

const apiService = {
    /**
        * Logs in a user. Uses base axios for specific headers.
        */
    async login(usernameInput: string, passwordInput: string): Promise<AuthResponse> {
        const params = new URLSearchParams();
        params.append('username', usernameInput);
        params.append('password', passwordInput);
        console.log(`[api.ts login] Attempting login for user: ${usernameInput}`); // LOGGING
        const response = await axios.post<AuthResponse>('/token', params, {
            baseURL: '/', // Use root base URL since '/token' is not under /api/v1
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        console.log(`[api.ts login] Login successful for user: ${usernameInput}`); // LOGGING
        return response.data;
    },

    /**
        * Validates the header of an uploaded file.
        */
    async validateUpload(formData: FormData): Promise<FileValidationResponse> {
        console.log('[api.ts validateUpload] Attempting file header validation...'); // LOGGING
        const response = await axiosInstance.post<FileValidationResponse>('/validate-upload', formData, {
             headers: { 'Content-Type': undefined } // Let browser set Content-Type for FormData
        });
        console.log(`[api.ts validateUpload] Validation response received: isValid=${response.data.is_valid}`); // LOGGING
        return response.data;
    },


    /**
        * Uploads the vendor file (after validation).
        * Returns the full JobResponse object.
        */
    async uploadFile(formData: FormData): Promise<JobResponse> { // Return JobResponse
        console.log('[api.ts uploadFile] Attempting file upload...'); // LOGGING
        const response = await axiosInstance.post<JobResponse>('/upload', formData, { // Expect JobResponse
                headers: { 'Content-Type': undefined } // Let browser set Content-Type for FormData
        });
        console.log(`[api.ts uploadFile] Upload successful, job ID: ${response.data.id}, Target Level: ${response.data.target_level}`); // LOGGING
        return response.data;
    },

    /**
        * Fetches the status and details of a specific job.
        */
    async getJobStatus(jobId: string): Promise<JobDetails> {
        console.log(`[api.ts getJobStatus] Fetching status for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get<JobDetails>(`/jobs/${jobId}`);
        console.log(`[api.ts getJobStatus] Received status for job ${jobId}:`, response.data.status, `Target Level: ${response.data.target_level}`, `Job Type: ${response.data.job_type}`); // LOGGING
        return response.data;
    },

    /**
        * Fetches statistics for a specific job.
        */
    async getJobStats(jobId: string): Promise<JobStatsData> { // Use the updated interface here
        console.log(`[api.ts getJobStats] Fetching stats for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get<JobStatsData>(`/jobs/${jobId}/stats`);
        console.log(`[api.ts getJobStats] Received stats for job ${jobId}:`, JSON.parse(JSON.stringify(response.data)));
        return response.data;
    },

    /**
     * Fetches the detailed classification results for a specific job.
     * Returns the JobResultsResponse structure containing job type and results list.
     */
    async getJobResults(jobId: string): Promise<JobResultsResponse> {
        console.log(`[api.ts getJobResults] Fetching detailed results for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get<JobResultsResponse>(`/jobs/${jobId}/results`);
        console.log(`[api.ts getJobResults] Received ${response.data.results.length} detailed result items for job ${jobId} (Type: ${response.data.job_type}).`); // LOGGING
        return response.data;
    },

    /**
        * Requests email notification for a job completion.
        */
    async requestNotification(jobId: string, email: string): Promise<NotifyResponse> {
        console.log(`[api.ts requestNotification] Requesting notification for job ${jobId} to email ${email}`); // LOGGING
        const response = await axiosInstance.post<NotifyResponse>(`/jobs/${jobId}/notify`, { email });
        console.log(`[api.ts requestNotification] Notification request response:`, response.data.success); // LOGGING
        return response.data;
    },

    /**
        * Downloads the results file for a completed job.
        */
    async downloadResults(jobId: string): Promise<DownloadResult> {
        console.log(`[api.ts downloadResults] Requesting download for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get(`/jobs/${jobId}/download`, {
            responseType: 'blob',
        });
        const disposition = response.headers['content-disposition'];
        let filename = `results_${jobId}.xlsx`;
        if (disposition?.includes('attachment')) {
            const filenameMatch = disposition.match(/filename\*?=(?:(?:"((?:[^"\\]|\\.)*)")|(?:([^;\n]*)))/i);
            if (filenameMatch?.[1]) { filename = filenameMatch[1].replace(/\\"/g, '"'); }
            else if (filenameMatch?.[2]) {
                    const utf8Match = filenameMatch[2].match(/^UTF-8''(.*)/i);
                    if (utf8Match?.[1]) { try { filename = decodeURIComponent(utf8Match[1]); } catch (e) { filename = utf8Match[1]; } }
                    else { filename = filenameMatch[2]; }
            }
        }
        console.log(`[api.ts downloadResults] Determined download filename: ${filename}`); // LOGGING
        return { blob: response.data as Blob, filename };
    },

    /**
        * Fetches a list of jobs for the current user, with optional filtering/pagination.
        */
    async getJobs(params: GetJobsParams = {}): Promise<JobResponse[]> {
        const cleanedParams = Object.fromEntries(
            Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
        );
        console.log('[api.ts getJobs] Fetching job list with params:', cleanedParams); // LOGGING
        const response = await axiosInstance.get<JobResponse[]>('/jobs/', { params: cleanedParams });
        console.log(`[api.ts getJobs] Received ${response.data.length} jobs.`); // LOGGING
        return response.data;
    },

    // --- User Management API Methods ---

    /**
        * Fetches the current logged-in user's details.
        */
    async getCurrentUser(): Promise<UserResponse> {
        console.log('[api.ts getCurrentUser] Fetching current user details...'); // LOGGING
        const response = await axiosInstance.get<UserResponse>('/users/me');
        console.log(`[api.ts getCurrentUser] Received user: ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Fetches a list of all users (admin only).
        */
    async getUsers(skip: number = 0, limit: number = 100): Promise<UserResponse[]> {
        console.log(`[api.ts getUsers] Fetching user list (skip: ${skip}, limit: ${limit})...`); // LOGGING
        const response = await axiosInstance.get<UserResponse[]>('/users/', { params: { skip, limit } });
         console.log(`[api.ts getUsers] Received ${response.data.length} users.`); // LOGGING
        return response.data;
    },

        /**
        * Fetches a specific user by ID (admin or self).
        */
        async getUserById(userId: string): Promise<UserResponse> {
        console.log(`[api.ts getUserById] Fetching user ID: ${userId}`); // LOGGING
        const response = await axiosInstance.get<UserResponse>(`/users/${userId}`);
        console.log(`[api.ts getUserById] Received user: ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Creates a new user (admin only).
        */
    async createUser(userData: UserCreateData): Promise<UserResponse> {
        console.log(`[api.ts createUser] Attempting to create user (admin): ${userData.username}`); // LOGGING
        const response = await axiosInstance.post<UserResponse>('/users/', userData);
        console.log(`[api.ts createUser] User created successfully (admin): ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Updates a user (admin or self).
        */
    async updateUser(userId: string, userData: UserUpdateData): Promise<UserResponse> {
        console.log(`[api.ts updateUser] Attempting to update user ID: ${userId}`); // LOGGING
        const response = await axiosInstance.put<UserResponse>(`/users/${userId}`, userData);
        console.log(`[api.ts updateUser] User updated successfully: ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Deletes a user (admin only).
        */
    async deleteUser(userId: string): Promise<{ message: string }> {
        console.log(`[api.ts deleteUser] Attempting to delete user ID: ${userId}`); // LOGGING
        const response = await axiosInstance.delete<{ message: string }>(`/users/${userId}`);
        console.log(`[api.ts deleteUser] User delete response: ${response.data.message}`); // LOGGING
        return response.data;
    },
    // --- END User Management API Methods ---

    // --- ADDED: Public Registration API Method ---
    /**
     * Registers a new user publicly.
     */
    async registerUser(userData: UserCreateData): Promise<UserResponse> {
        console.log(`[api.ts registerUser] Attempting public registration for user: ${userData.username}`);
        const response = await axiosInstance.post<UserResponse>('/users/register', userData);
        console.log(`[api.ts registerUser] Public registration successful: ${response.data.username}`);
        return response.data;
    },
    // --- END Public Registration API Method ---


    // --- ADDED: Password Reset API Methods ---
    /**
     * Requests a password reset email to be sent.
     */
    async requestPasswordRecovery(email: string): Promise<MessageResponse> {
        console.log(`[api.ts requestPasswordRecovery] Requesting password reset for email: ${email}`);
        const response = await axiosInstance.post<MessageResponse>('/auth/password-recovery', { email });
        console.log(`[api.ts requestPasswordRecovery] Request response: ${response.data.message}`);
        return response.data;
    },

    /**
     * Resets the password using the provided token and new password.
     */
    async resetPassword(token: string, newPassword: string): Promise<MessageResponse> {
        console.log(`[api.ts resetPassword] Attempting password reset with token: ${token.substring(0, 10)}...`);
        const response = await axiosInstance.post<MessageResponse>('/auth/reset-password', {
            token: token,
            new_password: newPassword
        });
        console.log(`[api.ts resetPassword] Reset response: ${response.data.message}`);
        return response.data;
    },
    // --- END Password Reset API Methods ---

    // --- ADDED: Reclassification API Method ---
    /**
     * Submits flagged items for reclassification.
     */
    async reclassifyJob(originalJobId: string, items: ReclassifyRequestItemData[]): Promise<ReclassifyResponseData> {
        console.log(`[api.ts reclassifyJob] Submitting ${items.length} items for reclassification for job ${originalJobId}`);
        const payload = { items: items };
        const response = await axiosInstance.post<ReclassifyResponseData>(`/jobs/${originalJobId}/reclassify`, payload);
        console.log(`[api.ts reclassifyJob] Reclassification job started: ${response.data.review_job_id}`);
        return response.data;
    },
    // --- END ADDED ---

    // --- ADDED: Admin Cache API Methods ---
    /**
     * Fetches a paginated list of cached vendor classifications (admin only).
     */
    async getCacheEntries(params: GetCacheEntriesParams = {}): Promise<PaginatedVendorCacheResponse> {
        const cleanedParams = Object.fromEntries(
            Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
        );
        console.log('[api.ts getCacheEntries] Fetching cache entries with params:', cleanedParams);
        // Uses axiosInstance, requires admin auth token via interceptor
        const response = await axiosInstance.get<PaginatedVendorCacheResponse>('/admin/cache/', { params: cleanedParams });
        console.log(`[api.ts getCacheEntries] Received ${response.data.items.length} cache entries (Total: ${response.data.total}).`);
        return response.data;
    },

    /**
     * Fetches a specific cached vendor classification by name (admin only).
     */
    async getCacheEntry(normalizedVendorName: string): Promise<VendorCacheItem> {
        console.log(`[api.ts getCacheEntry] Fetching cache entry for: ${normalizedVendorName}`);
        const encodedName = encodeURIComponent(normalizedVendorName); // Ensure name is URL-safe
        const response = await axiosInstance.get<VendorCacheItem>(`/admin/cache/${encodedName}`);
        console.log(`[api.ts getCacheEntry] Received cache entry for: ${response.data.normalized_vendor_name}`);
        return response.data;
    },

    // --- Placeholder for future Admin cache actions ---
    // async updateCacheEntry(normalizedVendorName: string, updateData: any): Promise<VendorCacheItem> {
    //     console.log(`[api.ts updateCacheEntry] Attempting to update cache entry: ${normalizedVendorName}`);
    //     const encodedName = encodeURIComponent(normalizedVendorName);
    //     const response = await axiosInstance.put<VendorCacheItem>(`/admin/cache/${encodedName}`, updateData);
    //     console.log(`[api.ts updateCacheEntry] Cache entry updated: ${response.data.normalized_vendor_name}`);
    //     return response.data;
    // },
    // async deleteCacheEntry(normalizedVendorName: string): Promise<void> {
    //     console.log(`[api.ts deleteCacheEntry] Attempting to delete cache entry: ${normalizedVendorName}`);
    //     const encodedName = encodeURIComponent(normalizedVendorName);
    //     await axiosInstance.delete(`/admin/cache/${encodedName}`);
    //     console.log(`[api.ts deleteCacheEntry] Cache entry deleted: ${normalizedVendorName}`);
    // },
    // --- END ADDED: Admin Cache API Methods ---

};

export default apiService;

// Re-export specific types needed by components/stores
export type {
    UserResponse, UserCreateData, UserUpdateData, JobResponse, JobStatsData,
    FileValidationResponse, JobResultsResponse, ReclassifyRequestItemData,
    VendorCacheItem, PaginatedVendorCacheResponse, GetCacheEntriesParams
};
```

```vue
<!-- <file path='frontend/vue_frontend/src/components/UserManagement.vue'> -->
<template>
    <div class="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
    <div class="bg-gray-100 text-gray-800 p-4 sm:p-5 border-b border-gray-200 flex justify-between items-center">
        <h4 class="text-xl font-semibold mb-0">User Management</h4>
        <button
        @click="openCreateModal"
        class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
        >
        <PlusIcon class="h-5 w-5 mr-2 -ml-1" />
        Create User
        </button>
    </div>

    <div class="p-6 sm:p-8">
        <!-- Loading State -->
        <div v-if="isLoading" class="text-center text-gray-500 py-8">
        <svg class="animate-spin inline-block h-6 w-6 text-primary mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Loading users...</span>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="p-4 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm flex items-center">
        <ExclamationTriangleIcon class="h-5 w-5 mr-2 text-red-600 flex-shrink-0"/>
        <span>Error loading users: {{ error }}</span>
        </div>

        <!-- Empty State -->
        <div v-else-if="!users || users.length === 0" class="text-center text-gray-500 py-8">
        <p>No users found.</p>
        <p class="text-sm">Click 'Create User' to add the first user.</p>
        </div>

        <!-- User Table -->
        <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
            <tr>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Full Name</th>
                <th scope="col" class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Active</th>
                <th scope="col" class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Admin</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                <th scope="col" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{{ user.username }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ user.email }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ user.full_name || '-' }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-center">
                <span :class="user.is_active ? 'text-green-600' : 'text-red-600'">
                    <CheckCircleIcon v-if="user.is_active" class="h-5 w-5 inline-block" />
                    <XCircleIcon v-else class="h-5 w-5 inline-block" />
                </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-center">
                    <span :class="user.is_superuser ? 'text-indigo-600' : 'text-gray-400'">
                    <ShieldCheckIcon v-if="user.is_superuser" class="h-5 w-5 inline-block" />
                    <ShieldExclamationIcon v-else class="h-5 w-5 inline-block" />
                    </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDateTime(user.created_at) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm font-medium space-x-2">
                <button @click="openEditModal(user)" class="text-indigo-600 hover:text-indigo-800" title="Edit User">
                    <PencilSquareIcon class="h-5 w-5 inline-block" />
                </button>
                <button
                    @click="confirmDelete(user)"
                    :disabled="user.username === authStore.username"
                    class="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Delete User"
                >
                    <TrashIcon class="h-5 w-5 inline-block" />
                </button>
                </td>
            </tr>
            </tbody>
        </table>
        </div>
        <!-- TODO: Add Pagination Controls -->
    </div>

    <!-- Create/Edit User Modal -->
    <UserFormModal
        :show="showModal"
        :user-to-edit="userToEdit"
        @close="closeModal"
        @save="handleSaveUser"
    />

    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import apiService, { type UserResponse, type UserCreateData, type UserUpdateData } from '@/services/api';
import { useAuthStore } from '@/stores/auth';
import UserFormModal from './UserFormModal.vue'; // Assume this component exists
import {
    PlusIcon, PencilSquareIcon, TrashIcon, CheckCircleIcon, XCircleIcon,
    ExclamationTriangleIcon, ShieldCheckIcon, ShieldExclamationIcon
} from '@heroicons/vue/24/outline'; // Use outline icons

const authStore = useAuthStore();
const users = ref<UserResponse[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const showModal = ref(false);
const userToEdit = ref<UserResponse | null>(null);

const fetchUsers = async () => {
    isLoading.value = true;
    error.value = null;
    try {
    users.value = await apiService.getUsers();
    } catch (err: any) {
    error.value = err.message || 'Failed to load users.';
    } finally {
    isLoading.value = false;
    }
};

const openCreateModal = () => {
    userToEdit.value = null;
    showModal.value = true;
};

const openEditModal = (user: UserResponse) => {
    userToEdit.value = { ...user }; // Clone user data
    showModal.value = true;
};

const closeModal = () => {
    showModal.value = false;
    userToEdit.value = null;
};

const handleSaveUser = async (userData: UserCreateData | UserUpdateData) => {
    isLoading.value = true; // Consider a different loading state for modal actions
    error.value = null; // Clear main table error
    try {
        if (userToEdit.value) {
            // Update user
            await apiService.updateUser(userToEdit.value.id, userData as UserUpdateData);
        } else {
            // Create user
            await apiService.createUser(userData as UserCreateData);
        }
        closeModal();
        await fetchUsers(); // Refresh the user list
    } catch (err: any) {
        // Handle error (maybe display in modal or globally)
        console.error("Failed to save user:", err);
        // For now, log it, ideally show in modal
        alert(`Error saving user: ${err.message}`);
        // error.value = `Error saving user: ${err.message}`;
    } finally {
            isLoading.value = false;
    }
};

const confirmDelete = async (user: UserResponse) => {
    if (user.username === authStore.username) {
    alert("You cannot delete your own account.");
    return;
    }
    if (confirm(`Are you sure you want to delete user "${user.username}" (${user.email})? This action cannot be undone.`)) {
    isLoading.value = true; // Use main loading indicator for now
    error.value = null;
    try {
        await apiService.deleteUser(user.id);
        await fetchUsers(); // Refresh list
    } catch (err: any) {
        error.value = `Failed to delete user: ${err.message}`;
    } finally {
        isLoading.value = false;
    }
    }
};

    const formatDateTime = (isoString: string | null | undefined): string => {
    if (!isoString) return 'N/A';
    try {
        return new Date(isoString).toLocaleDateString(undefined, {
            year: 'numeric', month: 'short', day: 'numeric'
        });
    } catch { return 'Invalid Date'; }
};


onMounted(() => {
    fetchUsers();
});
</script>
```

**Next Steps (Manual Implementation):**

1.  **Add Settings:** Add `CACHE_CONFIDENCE_THRESHOLD: float = 0.95` to your `app/core/config.py` -> `Settings` class.
2.  **Frontend Routing:**
    *   Import `AdminClassificationCache.vue` in your `frontend/vue_frontend/src/router/index.ts`.
    *   Add a new route definition within the `admin` section (or wherever your admin routes are defined), ensuring it has `meta: { requiresAuth: true, requiresAdmin: true }`:
        ```typescript
        {
          path: 'cache',
          name: 'AdminCache',
          component: () => import('@/components/AdminClassificationCache.vue'), // Lazy load
          meta: { requiresAuth: true, requiresAdmin: true, title: 'Classification Cache' }
        },
        ```
3.  **Frontend Navigation:** Add a `<router-link>` to the new `AdminCache` route in your admin layout/sidebar component (e.g., `AdminLayout.vue` or similar). This might look like:
    ```vue
     <router-link
        :to="{ name: 'AdminCache' }"
        class="flex items-center px-4 py-2 text-gray-700 rounded-md hover:bg-gray-200"
        active-class="bg-gray-200 font-semibold"
      >
        <DatabaseIcon class="h-5 w-5 mr-3" /> <!-- Or another suitable icon -->
        Classification Cache
      </router-link>
    ```
4.  **Testing:** Thoroughly test the cache query, population, and the admin view. Check logs for cache hits and population attempts.