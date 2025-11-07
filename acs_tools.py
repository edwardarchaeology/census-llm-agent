"""
ACS and TIGER/Line data fetching tools with caching.
Louisiana tracts only (state FIPS 22).
"""
import hashlib
import math
import os
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
import shapefile  # pyshp

CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

CENSUS_API_KEY = os.getenv("CENSUS_KEY")


def _get_cache_key(*args) -> str:
    """Generate cache key from arguments."""
    key_str = "_".join(str(arg) for arg in args)
    return hashlib.md5(key_str.encode()).hexdigest()[:16]


def fetch_acs_tracts_LA(
    year: int = 2023,
    var_ids: list[str] = None,
    county_fips: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch ACS 5-year estimates for Louisiana census tracts.
    
    Args:
        year: ACS year (default 2023)
        var_ids: List of variable IDs to fetch
        county_fips: Optional county FIPS to filter (e.g., "071" for Orleans Parish)
    
    Returns:
        DataFrame with GEOID, NAME, and requested variables
    """
    if var_ids is None:
        var_ids = []
    
    # Generate cache key
    cache_key = _get_cache_key("acs", year, county_fips, *sorted(var_ids))
    cache_file = CACHE_DIR / f"acs_tracts_{cache_key}.csv"
    
    if cache_file.exists():
        print(f"Loading cached ACS data...")
        return pd.read_csv(cache_file, dtype={"GEOID": str, "state": str, "county": str, "tract": str})
    
    # Build API request
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    
    # Variables to fetch (always include NAME)
    get_vars = ["NAME"] + var_ids
    get_param = ",".join(get_vars)
    
    # Geography parameters
    params = {
        "get": get_param,
        "for": "tract:*",
        "in": f"state:22"  # Louisiana
    }
    
    if county_fips:
        params["in"] = f"state:22 county:{county_fips}"
    
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY
    
    print(f"Fetching ACS data for {len(var_ids)} variables...")
    response = requests.get(base_url, params=params, timeout=60)
    response.raise_for_status()
    
    data = response.json()
    
    # Convert to DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Create GEOID (state + county + tract)
    df["GEOID"] = df["state"] + df["county"] + df["tract"]
    
    # Convert variable columns to numeric
    for var in var_ids:
        if var in df.columns:
            df[var] = pd.to_numeric(df[var], errors="coerce")
    
    # Save to cache
    df.to_csv(cache_file, index=False)
    print(f"Cached ACS data to {cache_file}")
    
    return df


def _calculate_polygon_area_km2(coords):
    """
    Calculate area of a polygon in km² using spherical approximation.
    Coords should be in lon/lat (EPSG:4269).
    Uses approximation for small areas on Earth's surface.
    """
    if not coords or len(coords) < 3:
        return 0.0
    
    # Convert to radians and calculate area using spherical excess
    # For small areas, we can use a simpler planar approximation
    # Convert degrees to approximate meters at latitude
    
    # Get center latitude for scaling
    lats = [p[1] for p in coords]
    center_lat = sum(lats) / len(lats)
    
    # Meters per degree at this latitude
    lat_rad = math.radians(center_lat)
    m_per_deg_lat = 111132.92 - 559.82 * math.cos(2 * lat_rad) + 1.175 * math.cos(4 * lat_rad)
    m_per_deg_lon = 111412.84 * math.cos(lat_rad) - 93.5 * math.cos(3 * lat_rad)
    
    # Calculate area using shoelace formula
    area_deg2 = 0.0
    for i in range(len(coords)):
        j = (i + 1) % len(coords)
        area_deg2 += coords[i][0] * coords[j][1]
        area_deg2 -= coords[j][0] * coords[i][1]
    area_deg2 = abs(area_deg2) / 2.0
    
    # Convert to km²
    area_m2 = area_deg2 * m_per_deg_lon * m_per_deg_lat
    area_km2 = area_m2 / 1_000_000
    
    return area_km2


def fetch_tiger_tract_areas_LA(vintage: int = 2024) -> pd.DataFrame:
    """
    Fetch TIGER/Line tract shapefiles for Louisiana and compute area in km².
    Uses pyshp (shapefile) library - no GDAL required.
    
    Args:
        vintage: TIGER/Line vintage year (default 2024)
    
    Returns:
        DataFrame with GEOID and area_km2
    """
    cache_file = CACHE_DIR / f"tiger_tract_areas_la_{vintage}.csv"
    
    if cache_file.exists():
        print(f"Loading cached TIGER tract areas...")
        return pd.read_csv(cache_file, dtype={"GEOID": str})
    
    # Download TIGER/Line tract shapefile for Louisiana
    url = f"https://www2.census.gov/geo/tiger/TIGER{vintage}/TRACT/tl_{vintage}_22_tract.zip"
    
    print(f"Downloading TIGER/Line tract data for Louisiana (vintage {vintage})...")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    
    # Extract and read shapefile
    print("Computing tract areas...")
    areas = []
    
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        # Extract to temporary directory
        temp_dir = CACHE_DIR / f"temp_tiger_{vintage}"
        temp_dir.mkdir(exist_ok=True)
        z.extractall(temp_dir)
        
        # Find the .shp file
        shp_file = list(temp_dir.glob("*.shp"))[0]
        
        # Read with pyshp
        sf = shapefile.Reader(str(shp_file))
        
        # Get field names
        field_names = [field[0] for field in sf.fields[1:]]  # Skip DeletionFlag
        geoid_idx = field_names.index("GEOID")
        
        # Process each shape
        for shape_record in sf.shapeRecords():
            geoid = shape_record.record[geoid_idx]
            
            # Calculate area from polygon coordinates
            # Shape.points gives us the vertices, shape.parts tells us where each ring starts
            points = shape_record.shape.points
            parts = shape_record.shape.parts
            
            total_area = 0.0
            
            # Handle multipart polygons
            for i in range(len(parts)):
                start = parts[i]
                end = parts[i + 1] if i + 1 < len(parts) else len(points)
                ring_coords = points[start:end]
                
                # Calculate area for this ring
                area = _calculate_polygon_area_km2(ring_coords)
                total_area += area
            
            areas.append({"GEOID": geoid, "area_km2": total_area})
        
        # Close the shapefile reader explicitly
        sf.close()
    
    # Clean up temp directory (with retry on Windows)
    import shutil
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            shutil.rmtree(temp_dir)
            break
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(0.5)  # Wait a bit for file handles to close
            else:
                print(f"Warning: Could not delete temp directory {temp_dir}")
    
    # Create result DataFrame
    result = pd.DataFrame(areas)
    
    # Save to cache
    result.to_csv(cache_file, index=False)
    print(f"Cached tract areas to {cache_file}")
    
    return result


def fetch_data_for_query(
    var_ids: list[str],
    year: int = 2023,
    county_fips: Optional[str] = None,
    needs_area: bool = False
) -> pd.DataFrame:
    """
    Fetch all data needed for a query (ACS variables + optional tract areas).
    
    Args:
        var_ids: List of ACS variable IDs
        year: ACS year
        county_fips: Optional county filter
        needs_area: Whether to join tract area data
    
    Returns:
        DataFrame with GEOID, NAME, variables, and optionally area_km2
    """
    # Fetch ACS data
    df = fetch_acs_tracts_LA(year=year, var_ids=var_ids, county_fips=county_fips)
    
    # Optionally join area data
    if needs_area:
        area_df = fetch_tiger_tract_areas_LA(vintage=2024)
        df = df.merge(area_df, on="GEOID", how="left")
    
    return df
