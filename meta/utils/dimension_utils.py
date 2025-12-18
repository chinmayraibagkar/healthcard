"""
Creative Dimension Utilities for Meta HealthCard
Handles creative dimension classification and compliance checking
"""

from typing import Tuple, Optional
from meta.config.constants import DIMENSION_TOLERANCE


def classify_dimension(width: any, height: any) -> Tuple[Optional[str], bool]:
    """
    Classify dimension as SQUARE, 4:5/PORTRAIT, or VERTICAL
    
    Args:
        width: Image/video width in pixels
        height: Image/video height in pixels
    
    Returns:
        Tuple of (dimension_type, is_valid)
        - dimension_type: 'SQUARE', '4X5', 'VERTICAL', or None
        - is_valid: True if dimension is compliant, False otherwise
    
    Handles margin errors like 700x1280 ≈ 720x1280 with 5% tolerance
    """
    try:
        if not width or not height:
            return (None, False)
        
        w, h = int(width), int(height)
        
        if w == 0 or h == 0:
            return (None, False)
        
        ratio = h / w if w > 0 else 0
        
        # Square check (1:1 ratio) - allow 5% tolerance
        # Target: 1080x1080, 1200x1200, etc.
        # Tolerance allows 1026-1134 for 1080
        if abs(w - h) <= max(w, h) * DIMENSION_TOLERANCE:
            return ('SQUARE', True)
        
        # 4:5 vertical check - ratio should be ~1.25
        # Target: 1080x1350, 1200x1500, etc.
        # Allow ratios from 1.15 to 1.35
        if h > w and 1.15 <= ratio <= 1.35:
            return ('4X5', True)
        
        # General vertical check - height > width (any other vertical format)
        # This catches 9:16 (1080x1920, 720x1280, etc.) and similar
        if h > w:
            return ('VERTICAL', True)
        
        return (None, False)
    
    except:
        return (None, False)


def is_dimension_compliant(width: any, height: any) -> bool:
    """
    Check if dimension is square, 4:5, or vertical (legacy function).
    
    Args:
        width: Image/video width
        height: Image/video height
    
    Returns:
        True if dimension meets any standard format, False otherwise
    """
    dim_type, is_valid = classify_dimension(width, height)
    return is_valid and dim_type in ('SQUARE', '4X5', 'VERTICAL')


def check_ad_dimension_compliance(image_dims: str, video_dims: str) -> bool:
    """
    Check if ad is compliant with Meta's creative dimension requirements.
    
    Compliance requirements:
    - At least 1 square/4x5 dimension AND
    - At least 1 other vertical format
    - Minimum 2 dimensions total
    
    Args:
        image_dims: Pipe-separated image dimensions (e.g., "1080x1080|1080x1920")
        video_dims: Pipe-separated video dimensions (e.g., "1080x1920")
    
    Returns:
        True if ad meets dimension compliance requirements, False otherwise
    """
    categories = {'SQUARE': 0, '4X5': 0, 'VERTICAL': 0}
    
    def process_dims(dims_str: str):
        """Process dimension string and count by category"""
        if not dims_str or dims_str in ['NO_IMAGES', 'NO_VIDEOS', 'NO_MATCH', '']:
            return
        
        for d in dims_str.split('|'):
            d = d.strip()
            if 'x' in d:
                parts = d.split('x')
                if len(parts) == 2:
                    dim_type, is_valid = classify_dimension(parts[0], parts[1])
                    if is_valid and dim_type:
                        categories[dim_type] += 1
    
    # Process both image and video dimensions
    process_dims(image_dims)
    process_dims(video_dims)
    
    # Compliance logic:
    # - At least 1 square/4x5 dimension
    # - At least 1 vertical dimension (any type including 4x5)
    # - Minimum 2 compliant dimensions total
    has_square_or_4x5 = categories['SQUARE'] + categories['4X5'] >= 1
    has_vertical = categories['4X5'] + categories['VERTICAL'] >= 1
    total_compliant = sum(categories.values())
    
    # Need minimum 2 compliant dimensions with diversity requirement
    return total_compliant >= 2 and has_square_or_4x5 and has_vertical


def parse_dimension_string(dim_str: str) -> list:
    """
    Parse a pipe-separated dimension string into list of (width, height) tuples.
    
    Args:
        dim_str: String like "1080x1080|1080x1920"
    
    Returns:
        List of (width, height) tuples
    """
    if not dim_str or dim_str in ['NO_IMAGES', 'NO_VIDEOS', 'NO_MATCH', '']:
        return []
    
    dimensions = []
    for d in dim_str.split('|'):
        d = d.strip()
        if 'x' in d:
            parts = d.split('x')
            if len(parts) == 2:
                try:
                    w = int(parts[0])
                    h = int(parts[1])
                    dimensions.append((w, h))
                except:
                    pass
    
    return dimensions


def get_dimension_summary(image_dims: str, video_dims: str) -> dict:
    """
    Get a summary of dimensions across images and videos.
    
    Returns:
        Dictionary with counts by dimension type and compliance status
    """
    categories = {'SQUARE': 0, '4X5': 0, 'VERTICAL': 0, 'OTHER': 0}
    
    all_dims = []
    if image_dims and image_dims not in ['NO_IMAGES', 'NO_MATCH', '']:
        all_dims.extend(parse_dimension_string(image_dims))
    if video_dims and video_dims not in ['NO_VIDEOS', 'NO_MATCH', '']:
        all_dims.extend(parse_dimension_string(video_dims))
    
    for w, h in all_dims:
        dim_type, is_valid = classify_dimension(w, h)
        if is_valid and dim_type:
            categories[dim_type] += 1
        else:
            categories['OTHER'] += 1
    
    is_compliant = check_ad_dimension_compliance(image_dims, video_dims)
    
    return {
        'square_count': categories['SQUARE'],
        '4x5_count': categories['4X5'],
        'vertical_count': categories['VERTICAL'],
        'other_count': categories['OTHER'],
        'total_count': sum(categories.values()),
        'is_compliant': is_compliant
    }
